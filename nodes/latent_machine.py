import torch
import torch.fft
import random

class Latent_Machine:
    """
    Creates an empty latent initialized with Power-Law (1/f) noise, Perlin-like noise, or Plasma noise.
    Supports 4-channel (SD1.5/SDXL) and 16-channel (Flux/SD3) latents.
    """
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 64}),
                "model_type": ([
                    "SD1.5/SDXL/PicsArt/Kolors/Auraflow (4ch)",
                    "Flux/Qwen/SD3/Lumina (16ch)"
                ],),
                "noise_type": ([
                    "Gaussian (White): Sharp Architecture, Text, intricate mechanics",
                    "Pink (1/f): Photorealism, Portraits, Nature",
                    "Brown (1/f²): Anime, Digital Art, Bokeh/Backgrounds",
                    "Perlin : Fantasy landscapes, Fluids, Hair/Fabric",
                    "Plasma : Sci-Fi, Abstract, Alien terrain"
                ],),
                "intensity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "generate_noise"
    CATEGORY = "SATA_UtilityNode"

    def generate_noise(self, width, height, batch_size, model_type, noise_type, intensity, seed):
        # Set seed for reproducibility
        torch.manual_seed(seed)
        random.seed(seed)
        
        # Determine channels based on model type
        if "16ch" in model_type:
            c = 16
        else:
            c = 4
            
        # Latent dimensions (compressed by 8)
        h = height // 8
        w = width // 8
        
        # Generate base noise
        if "Gaussian" in noise_type:
            noise = torch.randn((batch_size, c, h, w), device=self.device)
            
        elif "Perlin" in noise_type:
            # Multi-Octave Value Noise Approximation
            noise = self.generate_perlin_approx(batch_size, c, h, w)
            
        else:
            # FFT-based Power Law Noise (Pink, Brown, Plasma)
            if "Pink" in noise_type:
                alpha = 1.0
            elif "Brown" in noise_type:
                alpha = 2.0
            elif "Plasma" in noise_type:
                alpha = 3.0 # Very smooth
            else:
                alpha = 0.0 # Fallback to white
                
            noise = self.generate_power_law_noise(batch_size, c, h, w, alpha)

        # Normalize standard deviation to match expected latent variance (approx 1.0 for standard Gaussian)
        # This ensures intensity works consistently across different noise types
        current_std = noise.std()
        if current_std > 1e-6:
            noise = noise / current_std
            
        # Apply intensity
        noise = noise * intensity

        return ({"samples": noise},)

    def generate_power_law_noise(self, batch_size, c, h, w, alpha):
        # Generate White Noise (Standard Gaussian)
        white_noise = torch.randn((batch_size, c, h, w), device=self.device)
        
        # Convert to Frequency Domain (FFT)
        fft_noise = torch.fft.fft2(white_noise)
        
        # Create Frequency Grid
        y = torch.fft.fftfreq(h, device=self.device)
        x = torch.fft.fftfreq(w, device=self.device)
        dy, dx = torch.meshgrid(y, x, indexing='ij')
        
        # Calculate distance from center (frequency magnitude)
        # Add epsilon to avoid division by zero at DC component
        frequency_magnitude = torch.sqrt(dy**2 + dx**2) + 1e-8
        
        # Apply Power Law Scaling: Amplitude ~ 1 / f^(alpha/2)
        scale = 1.0 / (frequency_magnitude ** (alpha / 2.0))
        
        # Zero out the DC component (mean brightness) to keep it neutral
        scale[0, 0] = 0 
        
        fft_structured = fft_noise * scale
        
        # Convert back to Spatial Domain (Inverse FFT)
        structured_noise = torch.fft.ifft2(fft_structured).real
        
        return structured_noise

    def generate_perlin_approx(self, batch_size, c, h, w):
        """
        Generates a Perlin-like noise by blending upsampled noise from multiple octaves.
        This is faster than calculating actual Perlin noise per pixel on the CPU/GPU.
        """
        noise = torch.zeros((batch_size, c, h, w), device=self.device)
        
        # Octaves: scale down, generate noise, scale up
        octaves = [2, 4, 8, 16]
        weights = [0.5, 0.25, 0.125, 0.0625] # 1/f amplitude falloff
        
        total_weight = 0
        
        for scale, weight in zip(octaves, weights):
            # Calculate small dimensions
            sh, sw = max(1, h // scale), max(1, w // scale)
            
            # Generate random noise at this scale
            small_noise = torch.randn((batch_size, c, sh, sw), device=self.device)
            
            # Upsample to full size using bicubic interpolation for smoothness
            upsampled = torch.nn.functional.interpolate(
                small_noise, size=(h, w), mode='bicubic', align_corners=False
            )
            
            noise += upsampled * weight
            total_weight += weight
            
        # Add a bit of fine-grained white noise for texture
        noise += torch.randn((batch_size, c, h, w), device=self.device) * 0.05
        
        return noise
