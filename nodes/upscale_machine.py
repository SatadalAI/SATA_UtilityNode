import torch
import torch.nn.functional as F
import folder_paths
import comfy.utils
from comfy import model_management
from spandrel import ModelLoader


def generate_blue_noise(batch_size, c, h, w, device, beta=1.5):
    # Generate White Noise (Standard Gaussian)
    white_noise = torch.randn((batch_size, c, h, w), device=device)
    
    # Convert to Frequency Domain (FFT)
    fft_noise = torch.fft.fft2(white_noise)
    
    # Create Frequency Grid
    y = torch.fft.fftfreq(h, device=device)
    x = torch.fft.fftfreq(w, device=device)
    dy, dx = torch.meshgrid(y, x, indexing='ij')
    
    # Calculate distance from center (frequency magnitude)
    frequency_magnitude = torch.sqrt(dy**2 + dx**2)
    
    # Apply High-Pass Scaling: Amplitude ~ f^(beta/2)
    scale = frequency_magnitude ** (beta / 2.0)
    
    # Zero out DC component
    scale[0, 0] = 0 
    
    fft_structured = fft_noise * scale
    
    # Convert back to Spatial Domain (Inverse FFT)
    blue_noise = torch.fft.ifft2(fft_structured).real
    
    # Normalize standard deviation to ~1.0
    std = blue_noise.std()
    if std > 1e-6:
        blue_noise = blue_noise / std
        
    return blue_noise


def _make_gaussian_kernel(kernel_size, sigma, device):
    """Build a separable 2D Gaussian kernel tensor (1,1,k,k) on device."""
    k = kernel_size
    coords = torch.arange(k, dtype=torch.float32, device=device) - k // 2
    gauss_1d = torch.exp(-0.5 * (coords / sigma) ** 2)
    gauss_1d = gauss_1d / gauss_1d.sum()
    kernel_2d = gauss_1d[:, None] * gauss_1d[None, :]
    return kernel_2d.view(1, 1, k, k)


def fast_gaussian_blur_bchw(tensor_bchw, kernel_size=9, sigma=3.0):
    """
    Fast per-channel GPU Gaussian blur via depthwise convolution.
    Input/Output: BCHW float tensor. Kernel is always created on the same device.
    """
    device = tensor_bchw.device
    k = kernel_size
    kernel = _make_gaussian_kernel(k, sigma, device)            # on same device
    C = tensor_bchw.shape[1]
    kernel_c = kernel.expand(C, 1, k, k).to(device)            # guarantee same device
    pad = k // 2
    return F.conv2d(tensor_bchw.contiguous(), kernel_c, padding=pad, groups=C)


def resize_bchw(tensor_bchw, target_h, target_w):
    """
    Fast GPU resize — stays on device, no antialias overhead.
    Bilinear for downscale (smoother), bicubic for upscale (sharper).
    """
    in_h, in_w = tensor_bchw.shape[2], tensor_bchw.shape[3]
    if in_h == target_h and in_w == target_w:
        return tensor_bchw
    downscaling = (target_h < in_h) or (target_w < in_w)
    mode = 'bilinear' if downscaling else 'bicubic'
    return F.interpolate(tensor_bchw, size=(target_h, target_w), mode=mode, align_corners=False)


# ─────────────────────────────────────────────────────────────────────────────
# Architecture optimization profiles for spandrel models.
# Keys match the inner nn.Module class name (type(model.model).__name__).
#
# tile       : starting tile size for tiled inference (OOM fallback halves it)
# fp16_model : cast model weights to FP16 before inference (Tensor Core boost)
# compile    : torch.compile mode — 'reduce-overhead' for fixed-shape tiling
# ─────────────────────────────────────────────────────────────────────────────
ARCH_PROFILES = {
    # ── Fast CNN / RRDB models — full FP16 support, large tiles ──────────────
    "RRDBNet":      {"tile": 768,  "fp16_model": True,  "compile": "reduce-overhead"},  # ESRGAN, Real-ESRGAN
    "SRVGGNetCompact": {"tile": 896, "fp16_model": True, "compile": "reduce-overhead"},  # Real-ESRGAN Compact
    "SPAN":         {"tile": 896,  "fp16_model": True,  "compile": "reduce-overhead"},  # Swift, very fast
    "PLKSR":        {"tile": 768,  "fp16_model": False, "compile": "reduce-overhead"},  # Lightweight
    "RealPLKSR":    {"tile": 768,  "fp16_model": False, "compile": "reduce-overhead"},  # Lightweight photo
    "RCAN":         {"tile": 768,  "fp16_model": True,  "compile": "reduce-overhead"},  # Residual channel attn
    "SAFMN":        {"tile": 896,  "fp16_model": True,  "compile": "reduce-overhead"},  # Very fast
    "DITN":         {"tile": 768,  "fp16_model": True,  "compile": "reduce-overhead"},
    "CRAFT":        {"tile": 768,  "fp16_model": True,  "compile": "reduce-overhead"},
    "NAFNet":       {"tile": 768,  "fp16_model": True,  "compile": "reduce-overhead"},
    "OmniSR":       {"tile": 640,  "fp16_model": True,  "compile": "reduce-overhead"},
    "RGT":          {"tile": 640,  "fp16_model": True,  "compile": "reduce-overhead"},
    # ── Transformer / attention models — autocast only, conservative tiles ────
    "DAT":          {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},  # Dual Attention Transformer
    "DAT_S":        {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},
    "HAT":          {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},  # Hybrid Attention
    "HAT_L":        {"tile": 480,  "fp16_model": False, "compile": "reduce-overhead"},  # HAT Large — very heavy
    "SwinIR":       {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},  # Swin Transformer IR
    "Swin2SR":      {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},
    "SAN":          {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},  # Second-order Attn
    "DRCT":         {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},
    "ATD":          {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},
    "GRL":          {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},
    "FDAT":         {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},
    "AuraSR":       {"tile": 512,  "fp16_model": False, "compile": "reduce-overhead"},
}

# Fallback profile for any architecture not listed above.
# Uses supports_half from spandrel for fp16_model, 512 tile as safe default.
_DEFAULT_PROFILE = {"tile": 512, "fp16_model": None, "compile": "reduce-overhead"}


class Upscale_Machine:
    # Session-level cache: model object id -> torch.compile'd inner module
    # Avoids recompiling the same model on repeated runs in the same session.
    _compiled_cache: dict = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale_model": (folder_paths.get_filename_list("upscale_models"), {"default": None}),
                "chained_model": (["None"] + folder_paths.get_filename_list("upscale_models"), {"default": "None"}),
                "rescale_factor": ("FLOAT", {"default": 2.0, "min": 0.01, "max": 16.0, "step": 0.01}),
                "frequency_split": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "upscale"
    CATEGORY = "SATA_UtilityNode"

    def load_model(self, model_name):
        """Load ESRGAN/RealESRGAN/AESRGAN from the project's upscale_models folder."""
        if not model_name:
            raise ValueError("No upscale model selected or provided.")

        model_path = folder_paths.get_full_path("upscale_models", model_name)
        model_loader = ModelLoader()
        model = model_loader.load_from_file(model_path)

        if model is None:
            raise RuntimeError(f"Failed to load upscale model: {model_name}")

        model.eval()
        return model

    def _get_arch_profile(self, upscale_model):
        """
        Detects the model architecture and returns its optimisation profile.
        Detection priority:
          1. Inner nn.Module class name (most specific)
          2. spandrel supports_half flag (fallback for unknown architectures)
        """
        inner_cls = type(upscale_model.model).__name__
        profile = ARCH_PROFILES.get(inner_cls)
        if profile is None:
            # Unknown architecture — use spandrel flag for fp16 decision
            fp16_ok = getattr(upscale_model, "supports_half", False)
            profile = {**_DEFAULT_PROFILE, "fp16_model": fp16_ok}
        return inner_cls, profile

    def _get_compiled_model(self, upscale_model, compile_mode):
        """
        Returns a torch.compile()'d version of the model's inner nn.Module.
        Cached by object id — compiles once per session per loaded model.
        Falls back silently to eager mode if compile fails or Triton is missing.
        """
        inner = upscale_model.model
        cache_key = id(inner)
        if cache_key not in Upscale_Machine._compiled_cache:
            # Check for triton before attempting compile, as torch.compile is lazy
            # and will otherwise crash on the first tile execution on Windows.
            try:
                import triton
                has_triton = True
            except ImportError:
                has_triton = False

            if has_triton:
                try:
                    compiled = torch.compile(inner, mode=compile_mode, dynamic=False)
                    Upscale_Machine._compiled_cache[cache_key] = compiled
                except Exception as ex:
                    print(f"[Upscale_Machine] torch.compile unavailable ({ex}), using eager mode.")
                    Upscale_Machine._compiled_cache[cache_key] = inner
            else:
                print("[Upscale_Machine] Triton not installed (Windows), skipping torch.compile.")
                Upscale_Machine._compiled_cache[cache_key] = inner
                
        return Upscale_Machine._compiled_cache[cache_key]

    def upscale_with_model(self, upscale_model, image_bchw, device, pbar=None):
        """
        Architecture-aware tiled upscale:
          - Detects model type and loads optimisation profile
          - FP16 weights (Tensor Cores) for CNN models that support it
          - torch.autocast for mixed-precision on every tile (all architectures)
          - torch.compile fused graph (cached per session, falls back safely)
        Input:  image_bchw -> (B,C,H,W) float32 [0,1]
        Output: (B,C,H',W') float32 [0,1]
        """
        arch_name, profile = self._get_arch_profile(upscale_model)
        spandrel_supports_half = getattr(upscale_model, "supports_half", False)
        use_fp16   = profile["fp16_model"] and spandrel_supports_half
        tile       = profile["tile"]
        comp_mode  = profile["compile"]
        device_type = device.type if hasattr(device, "type") else str(device).split(":")[0]

        print(f"[Upscale_Machine] {arch_name} | "
              f"tile={tile} | fp16={'yes' if use_fp16 else 'no'} | compile={comp_mode}")

        upscale_model.to(device)
        if use_fp16:
            upscale_model.half()
            in_tensor = image_bchw.to(device).half()
        else:
            in_tensor = image_bchw.to(device).float()

        # Compile inner nn.Module once per session
        compiled_fn = self._get_compiled_model(upscale_model, comp_mode)

        try:
            overlap = 32
            oom = True
            while oom:
                try:
                    if not pbar:
                        steps = in_tensor.shape[0] * comfy.utils.get_tiled_scale_steps(
                            in_tensor.shape[3], in_tensor.shape[2], tile_x=tile, tile_y=tile, overlap=overlap
                        )
                        local_pbar = comfy.utils.ProgressBar(steps)
                    else:
                        local_pbar = pbar

                    import contextlib
                    # If model doesn't support fp16 (like DAT/HAT), autocast to fp16 will also cause NaNs.
                    # We only autocast if use_fp16 is True to be perfectly safe.
                    ctx = torch.autocast(device_type=device_type, dtype=torch.float16) if use_fp16 else contextlib.nullcontext()
                    
                    with ctx:
                        s = comfy.utils.tiled_scale(
                            in_tensor,
                            lambda a: compiled_fn(a),
                            tile_x=tile,
                            tile_y=tile,
                            overlap=overlap,
                            upscale_amount=getattr(upscale_model, "scale", 4),
                            pbar=local_pbar
                        )
                    oom = False
                except model_management.OOM_EXCEPTION as e:
                    model_management.soft_empty_cache()
                    tile //= 2
                    if tile < 128:
                        raise e
        finally:
            upscale_model.cpu().float()   # Always restore to FP32 on CPU

        return torch.clamp(s.float(), min=0.0, max=1.0)

    def _round_to_modulus(self, value, modulus):
        if modulus is None or modulus <= 1:
            return int(max(1, round(value)))
        return max(modulus, int(round(value / modulus)) * modulus)

    def upscale(self, image, upscale_model, chained_model="None", rounding_modulus=8, supersample='true',
                rescale_factor=2.0, frequency_split=True):

        if image.ndim != 4:
            raise ValueError("Expected IMAGE tensor with 4 dims (B,H,W,C).")

        device = model_management.get_torch_device()

        original_height = int(image.shape[1])
        original_width = int(image.shape[2])
        target_w = self._round_to_modulus(original_width * rescale_factor, rounding_modulus)
        target_h = self._round_to_modulus(original_height * rescale_factor, rounding_modulus)

        # Move to GPU once as BCHW — stay there the entire pipeline
        current_bchw = image.movedim(-1, 1).to(device)
        if current_bchw.shape[1] == 1:
            current_bchw = current_bchw.repeat(1, 3, 1, 1)
        elif current_bchw.shape[1] > 3:
            current_bchw = current_bchw[:, :3, :, :]

        # Keep a clean GPU copy of original for frequency split baseline
        original_bchw = current_bchw.clone()

        # ── First upscale model ───────────────────────────────────────────────
        if upscale_model:
            up_model = self.load_model(upscale_model)
            current_bchw = self.upscale_with_model(up_model, current_bchw, device)
            # tiled_scale may return CPU tensor — pin back to GPU
            current_bchw = current_bchw.to(device)
            current_bchw = resize_bchw(current_bchw, target_h, target_w)

        # ── Chained model ─────────────────────────────────────────────────────
        has_chain = chained_model and chained_model != "None"
        if has_chain:
            chain_model = self.load_model(chained_model)
            current_bchw = self.upscale_with_model(chain_model, current_bchw, device)
            # tiled_scale may return CPU tensor — pin back to GPU
            current_bchw = current_bchw.to(device)
            current_bchw = resize_bchw(current_bchw, target_h, target_w)

        images_out = current_bchw

        # ── Frequency-Split SR ────────────────────────────────────────────────
        if frequency_split and upscale_model:
            # Ensure both tensors are on the same device before any arithmetic
            bicubic_bchw = resize_bchw(original_bchw.to(device), target_h, target_w)
            images_out = images_out.to(device)

            sr_low  = fast_gaussian_blur_bchw(images_out)
            sr_high = images_out - sr_low

            bic_low = fast_gaussian_blur_bchw(bicubic_bchw)
            images_out = torch.clamp(bic_low + sr_high, 0.0, 1.0)

        # ── Blue Noise realism (chained only) ─────────────────────────────────
        if has_chain:
            images_out = images_out.to(device)
            B, C, H, W = images_out.shape
            noise = generate_blue_noise(B, C, H, W, device)
            images_out = torch.clamp(images_out + noise * 0.15, 0.0, 1.0)

        # Convert back to BHWC for ComfyUI
        return (images_out.movedim(1, -1).contiguous(),)