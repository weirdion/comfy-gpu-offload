# ComfyUI RunPod Remote Execution - Project Context

**Date**: 2025-01-16  
**Purpose**: Build a custom ComfyUI node for executing workflows on RunPod serverless GPU endpoints while maintaining local visual workflow iteration and preview capabilities.

---

## Table of Contents

1. [Project Goals](#project-goals)
2. [Use Case & Workflow](#use-case--workflow)
3. [Architecture Overview](#architecture-overview)
4. [Security Requirements](#security-requirements)
5. [Technical Implementation](#technical-implementation)
6. [Code Snippets](#code-snippets)
7. [API Documentation](#api-documentation)
8. [File Structure](#file-structure)
9. [Testing Strategy](#testing-strategy)
10. [Future Enhancements](#future-enhancements)

---

## Project Goals

### Primary Objectives

1. **Enable RunPod serverless execution from ComfyUI UI**
   - Execute heavy GPU workloads on RunPod without leaving ComfyUI
   - Maintain visual workflow design and iteration locally
   - Preview results immediately in ComfyUI interface

2. **Cost optimization through hybrid execution**
   - Fast local testing with lightweight models (SDXL Turbo, etc.)
   - Toggle to RunPod for high-quality final renders
   - Scale to zero when idle (serverless = pay only for compute used)

3. **Security-first design**
   - No API keys in workflow files (environment variables only)
   - No secrets committed to version control
   - Secure data handling (download → local filesystem → cleanup)

4. **Developer experience**
   - Clean, modular, maintainable code
   - Comprehensive error handling and logging
   - Easy installation and configuration

### Non-Goals

- ❌ Not building a general-purpose ComfyUI API wrapper
- ❌ Not replacing local ComfyUI execution
- ❌ Not building a RunPod management dashboard

---

## Use Case & Workflow

### Target User

Personal use for AI image/video generation with:
- Local ComfyUI installation for workflow design
- RunPod account with serverless endpoint configured
- Need for visual feedback during iteration
- Cost-conscious approach to GPU usage

### Typical Workflow

```
1. Design workflow in ComfyUI locally
   ↓
2. Test with fast local model (SDXL Turbo, few steps)
   ↓
3. Satisfied with composition/prompt?
   ↓ YES
4. Toggle "Use RunPod" in custom node
   ↓
5. Execute on RunPod serverless (high-quality, many steps)
   ↓
6. Preview results in ComfyUI UI
   ↓
7. Save to local filesystem
   ↓
8. Iterate or finish
```

### Example Use Cases

- **Image editing**: Load image → apply style transfer → upscale 4x → preview
- **Video generation**: Text prompt → AnimateDiff workflow → 120 frames → preview
- **Batch variations**: Same workflow, 10 different seeds → overnight processing

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│  Local Machine                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ComfyUI (localhost:8188)                         │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  User's Visual Workflow                     │  │  │
│  │  │  ┌──────────┐    ┌──────────┐               │  │  │
│  │  │  │ Load IMG │───▶│  Prompt  │               │  │  │
│  │  │  └──────────┘    └─────┬────┘               │  │  │
│  │  │                         │                    │  │  │
│  │  │  ┌──────────────────────▼──────────────┐    │  │  │
│  │  │  │  RunPod Remote Execute Node        │    │  │  │
│  │  │  │  [enable_remote: ON/OFF]           │    │  │  │
│  │  │  └──────────────┬──────────────────────┘    │  │  │
│  │  │                 │                           │  │  │
│  │  │  ┌──────────────▼──────────────┐            │  │  │
│  │  │  │  Preview Image (local UI)   │            │  │  │
│  │  │  └─────────────────────────────┘            │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
│                         │                               │
│                         │ enable_remote=True            │
│                         │ (HTTPS/TLS)                   │
└─────────────────────────┼───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  RunPod Serverless Endpoint                             │
│  https://api.runpod.ai/v2/{endpoint_id}                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Worker (Flex - scales to zero)                    │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │  ComfyUI Worker Container                    │  │ │
│  │  │  - Custom nodes from Network Volume          │  │ │
│  │  │  - Models from Network Volume                │  │ │
│  │  │  - Executes workflow JSON                    │  │ │
│  │  │  - Returns base64 images                     │  │ │
│  │  └──────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Network Volume (persistent):                           │
│  /runpod-volume/ComfyUI/                                │
│    ├── models/                                          │
│    └── custom_nodes/                                    │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Local Mode** (enable_remote=False):
   - Execute workflow locally on CPU/local GPU
   - Use for fast iteration with lightweight models
   - Instant preview, no API calls

2. **Remote Mode** (enable_remote=True):
   - Node captures current workflow state
   - Serializes to API JSON format
   - Submits to RunPod via HTTPS POST
   - Polls status endpoint until completion
   - Downloads base64 images from response
   - Converts to ComfyUI IMAGE tensor format
   - Passes to Preview Image node for display

### Technology Stack

- **Language**: Python 3.10+
- **ComfyUI**: Custom node API
- **HTTP Client**: `requests` library
- **Image Processing**: PIL/Pillow, NumPy, PyTorch
- **Security**: Environment variables via `os.getenv()`
- **RunPod API**: REST API with Bearer token auth

---

## Security Requirements

### Critical Security Principles

1. **Never store secrets in code or workflow files**
   ```python
   # ✅ GOOD - Environment variable
   api_key = os.getenv("RUNPOD_API_KEY")
   
   # ❌ BAD - Hardcoded
   api_key = "runpod_abc123..."
   
   # ❌ BAD - Node input (saved to workflow file)
   "api_key": ("STRING", {"default": "hardcoded"})
   ```

2. **Validate all inputs**
   ```python
   if not api_key:
       raise ValueError(
           "RUNPOD_API_KEY not set! Add to environment:\n"
           "export RUNPOD_API_KEY='your_key_here'"
       )
   ```

3. **Secure file permissions**
   ```python
   # Downloaded outputs - owner read/write only
   output_path.chmod(0o600)
   ```

4. **HTTPS only for API calls**
   - All RunPod API communication over TLS
   - Verify SSL certificates (default in `requests`)

5. **Minimize data retention on cloud**
   - Use base64 response (not S3 storage)
   - Data downloaded directly to local machine
   - No persistent storage on RunPod after job completion

### Environment Variables Setup

**For Unix/Linux/Mac** (`run.sh`):
```bash
#!/bin/bash
export RUNPOD_API_KEY="your_api_key_here"
export RUNPOD_ENDPOINT_ID="your_endpoint_id_here"

python main.py --listen 0.0.0.0
```

**For Windows** (`run.bat`):
```batch
@echo off
set RUNPOD_API_KEY=your_api_key_here
set RUNPOD_ENDPOINT_ID=your_endpoint_id_here

python main.py --listen 0.0.0.0
```

**Alternative: `.env` file** (requires `python-dotenv`):
```bash
# ComfyUI/.env (add to .gitignore!)
RUNPOD_API_KEY=your_api_key_here
RUNPOD_ENDPOINT_ID=your_endpoint_id_here
```

---

## Technical Implementation

### ComfyUI Custom Node Basics

ComfyUI nodes are Python classes with specific structure:

```python
class MyCustomNode:
    @classmethod
    def INPUT_TYPES(cls):
        """Define node inputs (visible in UI)"""
        return {
            "required": {
                "param_name": ("TYPE", {"default": value}),
            },
            "optional": {
                "optional_param": ("TYPE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)  # Output socket types
    RETURN_NAMES = ("images",)  # Output socket labels
    FUNCTION = "execute"  # Method to call
    CATEGORY = "MyCategory"  # Menu location
    
    def execute(self, param_name, optional_param=None):
        """Execute the node logic"""
        # Your code here
        return (result,)  # Must return tuple
```

### ComfyUI Data Types

Key tensor formats:
- **IMAGE**: `torch.Tensor` shape `[B, H, W, C]`, values `0.0-1.0`, RGB
- **MASK**: `torch.Tensor` shape `[B, H, W]`, values `0.0-1.0`
- **LATENT**: Dictionary `{"samples": torch.Tensor}`
- **CONDITIONING**: List of conditioning tuples
- **STRING**: Regular Python string
- **INT**, **FLOAT**, **BOOLEAN**: Python primitives

### RunPod Serverless API Flow

```python
# 1. Submit workflow (async)
POST https://api.runpod.ai/v2/{endpoint_id}/run
Headers:
  Authorization: Bearer {api_key}
  Content-Type: application/json
Body:
  {
    "input": {
      "workflow": { ...comfyui_workflow_json... },
      "images": [  // optional for img2img
        {"name": "input.png", "image": "base64..."}
      ]
    }
  }

Response:
  {
    "id": "job-uuid-here",
    "status": "IN_QUEUE"
  }

# 2. Poll status
GET https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}
Headers:
  Authorization: Bearer {api_key}

Response (in progress):
  {
    "id": "job-uuid",
    "status": "IN_PROGRESS"
  }

Response (completed):
  {
    "id": "job-uuid",
    "status": "COMPLETED",
    "output": {
      "images": [
        {
          "filename": "output_001.png",
          "type": "base64",
          "data": "iVBORw0KGgoAAAANS..."
        }
      ]
    }
  }

Response (failed):
  {
    "id": "job-uuid",
    "status": "FAILED",
    "error": "Error message here"
  }
```

### Network Volume Setup (One-time)

RunPod Network Volumes provide persistent storage for models and custom nodes:

```bash
# 1. Create Network Volume in RunPod UI
#    - Name: comfyui-models
#    - Size: 50GB (adjust based on models)
#    - Data center: Choose closest or cheapest

# 2. Deploy temporary pod to populate volume
#    - Attach network volume
#    - Use any cheap GPU (just for file transfer)
#    - Connect via SSH or Jupyter

# 3. Populate the volume
cd /workspace  # On pod: /workspace maps to network volume
mkdir -p ComfyUI/models/{checkpoints,loras,vae,controlnet}
mkdir -p ComfyUI/custom_nodes

# Download models
cd ComfyUI/models/checkpoints
wget https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors

# Clone custom nodes
cd ../../custom_nodes
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite

# 4. Terminate temporary pod

# 5. Attach volume to serverless endpoint
#    - Endpoint settings → Advanced → Network Volume
#    - Container start command (critical!):
#      sh -c "ln -sf /runpod-volume/ComfyUI/* /comfyui/ && /start.sh"
```

---

## Code Snippets

### Core Node Structure

```python
# custom_nodes/comfyui-runpod-remote/runpod_remote.py

import os
import json
import base64
import requests
import time
import torch
import numpy as np
from PIL import Image
from io import BytesIO

class RunPodRemoteExecute:
    """
    Execute ComfyUI workflows on RunPod serverless endpoint.
    Maintains local visual workflow while offloading heavy compute.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "workflow_json": ("STRING", {
                    "multiline": True,
                    "default": "Paste API workflow JSON here"
                }),
                "enable_remote": ("BOOLEAN", {
                    "default": False,
                    "label_on": "🚀 RunPod",
                    "label_off": "⚡ Local"
                }),
            },
            "optional": {
                "input_images": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"
    CATEGORY = "RunPod"
    OUTPUT_NODE = True
    
    def execute(self, workflow_json, enable_remote, input_images=None):
        if not enable_remote:
            return self._execute_local()
        return self._execute_remote(workflow_json, input_images)
```

### API Communication

```python
def _execute_remote(self, workflow_json, input_images):
    """Execute on RunPod and return images as ComfyUI tensors"""
    
    # Get credentials from environment
    api_key = os.getenv("RUNPOD_API_KEY")
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
    
    if not api_key or not endpoint_id:
        raise ValueError(
            "Missing environment variables!\n"
            "Required: RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID"
        )
    
    # Parse workflow
    workflow = json.loads(workflow_json)
    
    # Prepare payload
    payload = {"input": {"workflow": workflow}}
    
    if input_images is not None:
        payload["input"]["images"] = self._encode_images(input_images)
    
    # Submit job
    base_url = f"https://api.runpod.ai/v2/{endpoint_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{base_url}/run",
        headers=headers,
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    job_id = response.json()["id"]
    
    print(f"🚀 RunPod job submitted: {job_id}")
    
    # Poll for completion
    images = self._poll_until_complete(base_url, headers, job_id)
    
    # Convert to ComfyUI tensor format
    return (self._images_to_tensor(images),)
```

### Polling Logic

```python
def _poll_until_complete(self, base_url, headers, job_id, timeout=600):
    """Poll RunPod status endpoint until job completes"""
    
    start_time = time.time()
    poll_interval = 3  # seconds
    last_status = None
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"{base_url}/status/{job_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        status = data.get("status")
        
        # Only print status changes to reduce spam
        if status != last_status:
            elapsed = int(time.time() - start_time)
            print(f"   [{elapsed}s] Status: {status}")
            last_status = status
        
        if status == "COMPLETED":
            print(f"✅ Completed in {int(time.time() - start_time)}s")
            return data["output"]["images"]
        
        elif status == "FAILED":
            error = data.get("error", "Unknown error")
            raise RuntimeError(f"RunPod job failed: {error}")
        
        time.sleep(poll_interval)
    
    raise TimeoutError(f"Job {job_id} exceeded {timeout}s timeout")
```

### Image Encoding (ComfyUI → API)

```python
def _encode_images(self, images):
    """Convert ComfyUI IMAGE tensor to base64 for API"""
    encoded = []
    
    # ComfyUI images: [B, H, W, C] in 0-1 range, float32, RGB
    batch_size = images.shape[0]
    
    for i in range(batch_size):
        # Extract single image and convert to uint8
        img_np = (images[i].cpu().numpy() * 255).astype(np.uint8)
        
        # Convert to PIL Image
        pil_img = Image.fromarray(img_np)
        
        # Encode to PNG in memory
        buffer = BytesIO()
        pil_img.save(buffer, format="PNG")
        
        # Base64 encode
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        encoded.append({
            "name": f"input_{i:03d}.png",
            "image": img_b64
        })
    
    return encoded
```

### Image Decoding (API → ComfyUI)

```python
def _images_to_tensor(self, images):
    """Convert base64 images from API to ComfyUI IMAGE tensor"""
    tensors = []
    
    for img_data in images:
        if img_data.get("type") != "base64":
            print(f"⚠️  Skipping non-base64 image")
            continue
        
        # Decode base64
        img_bytes = base64.b64decode(img_data["data"])
        
        # Load with PIL
        pil_img = Image.open(BytesIO(img_bytes))
        
        # Convert to RGB if needed
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # Convert to numpy array and normalize to 0-1
        img_np = np.array(pil_img).astype(np.float32) / 255.0
        
        # Convert to PyTorch tensor [H, W, C]
        img_tensor = torch.from_numpy(img_np)
        tensors.append(img_tensor)
    
    if not tensors:
        raise ValueError("No valid images returned from RunPod")
    
    # Stack into batch [B, H, W, C]
    return torch.stack(tensors)
```

### Error Handling

```python
def execute(self, workflow_json, enable_remote, input_images=None):
    """Main execution with comprehensive error handling"""
    
    try:
        if not enable_remote:
            return self._execute_local()
        
        return self._execute_remote(workflow_json, input_images)
    
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "RunPod API timeout. Check your internet connection "
            "or increase timeout in node settings."
        )
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise RuntimeError(
                "RunPod authentication failed. "
                "Check RUNPOD_API_KEY environment variable."
            )
        elif e.response.status_code == 404:
            raise RuntimeError(
                "RunPod endpoint not found. "
                "Check RUNPOD_ENDPOINT_ID environment variable."
            )
        else:
            raise RuntimeError(f"RunPod API error: {e}")
    
    except json.JSONDecodeError:
        raise ValueError(
            "Invalid workflow JSON. "
            "Export workflow from ComfyUI using 'Save (API Format)'"
        )
    
    except Exception as e:
        # Log full error for debugging
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        raise
```

### Node Registration

```python
# __init__.py

from .runpod_remote import RunPodRemoteExecute

NODE_CLASS_MAPPINGS = {
    "RunPodRemoteExecute": RunPodRemoteExecute
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RunPodRemoteExecute": "RunPod Remote Execute"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
```

---

## API Documentation

### RunPod API References

**Official Documentation**:
- RunPod Serverless Docs: https://docs.runpod.io/serverless/overview
- RunPod API Reference: https://docs.runpod.io/serverless/endpoints/send-requests
- Worker API format: https://github.com/runpod-workers/worker-comfyui

**Key Endpoints**:

1. **Submit Job** (Async)
   ```
   POST https://api.runpod.ai/v2/{endpoint_id}/run
   ```

2. **Submit Job** (Sync - waits up to 90s)
   ```
   POST https://api.runpod.ai/v2/{endpoint_id}/runsync
   ```

3. **Check Status**
   ```
   GET https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}
   ```

4. **Cancel Job**
   ```
   POST https://api.runpod.ai/v2/{endpoint_id}/cancel/{job_id}
   ```

**Request Size Limits**:
- `/run` endpoint: 10 MB
- `/runsync` endpoint: 20 MB

**Authentication**:
- Header: `Authorization: Bearer {api_key}`
- Get API key: RunPod Console → Settings → API Keys

### ComfyUI API References

**Official Documentation**:
- ComfyUI GitHub: https://github.com/comfyanonymous/ComfyUI
- Custom Node Development: https://docs.comfy.org/development/core-concepts/custom-nodes
- API Format Workflows: https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py

**Workflow Export**:
1. Design workflow in ComfyUI UI
2. Enable Dev Mode: Settings (gear icon) → Enable Dev mode
3. Export: Workflow menu → Save (API Format)
4. Saves as `workflow_api.json`

**Key Differences**:
- **Regular workflow**: Includes UI positioning, visual metadata
- **API workflow**: Minimal JSON with only node connections and values

### Python Libraries

**Required Dependencies**:
```
requests>=2.31.0     # HTTP client for RunPod API
Pillow>=10.0.0       # Image encoding/decoding
numpy>=1.24.0        # Array operations
torch>=2.0.0         # ComfyUI tensor format (already installed)
```

**Optional**:
```
python-dotenv>=1.0.0  # For .env file support
```

---

## File Structure

```
ComfyUI/
├── custom_nodes/
│   └── comfyui-runpod-remote/
│       ├── __init__.py              # Node registration
│       ├── runpod_remote.py         # Main node implementation
│       ├── requirements.txt         # Python dependencies
│       ├── README.md                # User documentation
│       ├── LICENSE                  # MIT or similar
│       └── .gitignore              # Ignore __pycache__, etc.
│
├── .env                             # Environment variables (gitignored!)
├── run.sh                          # Launch script with env vars
└── workflows/                      # User's workflow storage
    ├── img2img_upscale.json
    └── video_generation.json
```

### `.gitignore` Template

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Environment
.env
.venv
env/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
outputs/
temp/
*.log
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_runpod_remote.py

import pytest
import torch
import numpy as np
from runpod_remote import RunPodRemoteExecute

class TestImageConversion:
    """Test image encoding/decoding"""
    
    def test_encode_images(self):
        node = RunPodRemoteExecute()
        
        # Create dummy ComfyUI image tensor
        # Shape: [B, H, W, C], values 0-1
        dummy_img = torch.rand(1, 512, 512, 3)
        
        encoded = node._encode_images(dummy_img)
        
        assert len(encoded) == 1
        assert "name" in encoded[0]
        assert "image" in encoded[0]
        assert isinstance(encoded[0]["image"], str)  # base64
    
    def test_images_to_tensor(self):
        node = RunPodRemoteExecute()
        
        # Create dummy API response
        api_response = [{
            "type": "base64",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "filename": "test.png"
        }]
        
        tensor = node._images_to_tensor(api_response)
        
        assert isinstance(tensor, torch.Tensor)
        assert tensor.dim() == 4  # [B, H, W, C]
        assert tensor.dtype == torch.float32
        assert 0 <= tensor.min() <= 1
        assert 0 <= tensor.max() <= 1

class TestErrorHandling:
    """Test error conditions"""
    
    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
        
        node = RunPodRemoteExecute()
        
        with pytest.raises(ValueError, match="RUNPOD_API_KEY"):
            node.execute(
                workflow_json="{}",
                enable_remote=True
            )
    
    def test_invalid_json(self):
        node = RunPodRemoteExecute()
        
        with pytest.raises(ValueError, match="Invalid workflow JSON"):
            node.execute(
                workflow_json="not valid json{",
                enable_remote=True
            )
```

### Integration Tests

```python
# tests/test_integration.py

import os
import pytest
from runpod_remote import RunPodRemoteExecute

@pytest.mark.skipif(
    not os.getenv("RUNPOD_API_KEY"),
    reason="Requires RunPod API key"
)
class TestRunPodIntegration:
    """Integration tests with real RunPod API (slow, costs money)"""
    
    def test_simple_workflow_execution(self):
        """Test end-to-end workflow execution"""
        
        node = RunPodRemoteExecute()
        
        # Load a simple test workflow
        with open("tests/fixtures/simple_workflow.json") as f:
            workflow_json = f.read()
        
        # Execute (this will actually hit RunPod and cost ~$0.01)
        result = node.execute(
            workflow_json=workflow_json,
            enable_remote=True
        )
        
        images = result[0]
        assert isinstance(images, torch.Tensor)
        assert images.shape[0] >= 1  # At least one image
```

### Manual Testing Checklist

Before release:

- [ ] Install node in fresh ComfyUI installation
- [ ] Test with environment variables set
- [ ] Test with missing environment variables (should error gracefully)
- [ ] Test local mode (enable_remote=False)
- [ ] Test remote mode with simple workflow
- [ ] Test with input images (img2img)
- [ ] Test with video workflow (AnimateDiff)
- [ ] Verify outputs preview correctly in ComfyUI
- [ ] Test error handling (invalid endpoint, timeout, etc.)
- [ ] Verify no secrets in saved workflow files
- [ ] Check logs for sensitive data leakage

---

## Future Enhancements

### Phase 1 (MVP - Current)

- ✅ Basic remote execution
- ✅ Image input/output support
- ✅ Error handling
- ✅ Environment variable configuration

### Phase 2 (Nice to Have)

- [ ] **Auto-workflow capture**: Automatically serialize current workflow
  - No need to paste JSON manually
  - Introspect ComfyUI server state via API

- [ ] **Progress callbacks**: Show RunPod job progress in UI
  - WebSocket connection to status endpoint
  - Update progress bar in ComfyUI

- [ ] **Cost estimation**: Show estimated cost before execution
  - Calculate based on GPU type and estimated duration
  - Display in node UI

- [ ] **Workflow optimization**: Automatically optimize workflow for RunPod
  - Detect inefficiencies (unnecessary nodes, etc.)
  - Suggest optimizations

### Phase 3 (Advanced)

- [ ] **Batch processing**: Queue multiple variations
  - Different seeds, prompts, parameters
  - Process overnight

- [ ] **Result caching**: Avoid re-running identical workflows
  - Hash workflow + inputs
  - Check cache before submitting

- [ ] **Multi-endpoint support**: Route to different endpoints
  - Different GPU types for different tasks
  - Fallback to secondary endpoint if primary busy

- [ ] **S3 integration**: Optional S3 upload for large outputs
  - Videos, high-res images
  - Direct download URLs instead of base64

### Community Features

- [ ] Share workflows as templates
- [ ] RunPod marketplace integration
- [ ] Community model repository

---

## Implementation Notes

### Development Environment Setup

```bash
# 1. Clone ComfyUI (if not already installed)
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install ComfyUI dependencies
pip install -r requirements.txt

# 4. Create custom node directory
mkdir -p custom_nodes/comfyui-runpod-remote
cd custom_nodes/comfyui-runpod-remote

# 5. Initialize Git repository (for version control)
git init
git remote add origin https://github.com/yourusername/comfyui-runpod-remote.git

# 6. Create initial files
touch __init__.py runpod_remote.py requirements.txt README.md .gitignore

# 7. Install development dependencies
pip install requests pillow numpy torch pytest
pip freeze > requirements.txt
```

### Testing During Development

```bash
# Run ComfyUI with your custom node
cd /path/to/ComfyUI
python main.py --listen 0.0.0.0

# Open browser: http://localhost:8188
# Right-click → Add Node → RunPod → RunPod Remote Execute

# Watch logs in terminal for print() statements
```

### Debugging Tips

1. **Enable verbose logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Test API calls independently**:
   ```python
   # test_api.py
   import requests
   import os
   
   api_key = os.getenv("RUNPOD_API_KEY")
   endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
   
   response = requests.get(
       f"https://api.runpod.ai/v2/{endpoint_id}",
       headers={"Authorization": f"Bearer {api_key}"}
   )
   print(response.json())
   ```

3. **Validate workflow JSON**:
   ```python
   import json
   
   # Load and validate
   with open("workflow_api.json") as f:
       workflow = json.load(f)
   
   # Check structure
   print(f"Nodes: {len(workflow)}")
   for node_id, node_data in workflow.items():
       print(f"  {node_id}: {node_data.get('class_type')}")
   ```

### Performance Optimization

**Network Volume Best Practices**:
- Pre-download all models to volume (avoid download during execution)
- Use symlinks in container start command
- Keep volume size reasonable to reduce startup time

**Cold Start Optimization**:
- Use FlashBoot (enabled by default on RunPod)
- Keep Docker images small (< 20GB recommended)
- Pre-warm workers for production use (Active Workers)

**API Call Optimization**:
- Implement exponential backoff for status polling
- Use `/runsync` for quick jobs (< 90s)
- Batch multiple workflows if possible

---

## Troubleshooting Guide

### Common Issues

**Issue**: "RUNPOD_API_KEY not set"
- **Solution**: Add environment variable to launch script or `.env` file
- **Verify**: `echo $RUNPOD_API_KEY` (Unix) or `echo %RUNPOD_API_KEY%` (Windows)

**Issue**: "401 Unauthorized"
- **Solution**: API key is invalid or expired
- **Verify**: Check RunPod Console → Settings → API Keys
- **Fix**: Generate new key and update environment variable

**Issue**: "404 Endpoint not found"
- **Solution**: Endpoint ID is incorrect
- **Verify**: Check RunPod Console → Serverless → Your Endpoint
- **Fix**: Copy correct endpoint ID from URL or Overview page

**Issue**: Job times out
- **Solution**: Increase timeout in node settings
- **Check**: RunPod Console → Logs to see if job is actually running
- **Verify**: Network volume is attached and models are present

**Issue**: "No valid images returned"
- **Solution**: RunPod workflow might not have SaveImage node
- **Fix**: Ensure workflow has at least one SaveImage node
- **Debug**: Check RunPod logs for errors

**Issue**: Images look wrong/corrupted
- **Solution**: Check color space conversion (RGB vs BGR)
- **Verify**: PIL Image mode is 'RGB' before conversion
- **Debug**: Save intermediate images to disk for inspection

---

## Cost Estimation

### RunPod Pricing (Approximate)

**Flex Workers** (scale to zero):
- RTX 4090: ~$0.34/hr
- RTX 3090: ~$0.22/hr  
- A100 80GB: ~$1.64/hr
- H100: ~$2.50/hr

**Network Volume**:
- ~$0.10/GB/month
- 50GB volume = $5/month

**Example Monthly Cost** (personal use):
```
Assumptions:
- 10 workflows/day
- 30 days/month
- Average 2 minutes per workflow
- RTX 4090 ($0.34/hr)

Compute: 300 workflows × 2 min = 600 min = 10 hrs
Cost: 10 hrs × $0.34 = $3.40

Storage: 50GB volume = $5.00

Total: ~$8.40/month
```

Compare to RTX 4090 purchase: **$1,600+**  
Break-even: **~16 years** of personal use

---

## Security Checklist

Before deploying:

- [ ] API keys stored in environment variables only
- [ ] `.env` file added to `.gitignore`
- [ ] No hardcoded secrets in code
- [ ] No secrets in workflow JSON files
- [ ] HTTPS used for all API calls
- [ ] SSL certificates verified (default in `requests`)
- [ ] Input validation on all user inputs
- [ ] Error messages don't leak sensitive info
- [ ] File permissions set correctly (0o600 for outputs)
- [ ] Dependencies from trusted sources only
- [ ] Code review completed
- [ ] Security scan run (e.g., `bandit`)

---

## License & Attribution

**Recommended License**: MIT

Allows others to:
- Use commercially
- Modify
- Distribute
- Sublicense

**Dependencies to Credit**:
- ComfyUI (GPL-3.0)
- RunPod (Commercial service)
- Python `requests` library (Apache 2.0)
- Pillow (PIL License)

---

## Additional Resources

### Learning Resources

**ComfyUI**:
- ComfyUI Wiki: https://github.com/comfyanonymous/ComfyUI/wiki
- Community Custom Nodes: https://github.com/ltdrdata/ComfyUI-Manager
- Example Workflows: https://comfyworkflows.com/

**RunPod**:
- Documentation: https://docs.runpod.io/
- Blog: https://www.runpod.io/blog
- Discord: https://discord.gg/runpod

**Python Development**:
- Requests docs: https://requests.readthedocs.io/
- Pillow docs: https://pillow.readthedocs.io/
- PyTorch docs: https://pytorch.org/docs/

### Community

- ComfyUI Discord: https://discord.gg/comfyui
- r/StableDiffusion: https://reddit.com/r/StableDiffusion
- r/comfyui: https://reddit.com/r/comfyui

---

## Questions for LLM (Claude Code)

When starting implementation, consider:

1. **Should we support workflow auto-capture** (introspect ComfyUI server) or require manual JSON paste?
   - Auto-capture: More UX friendly, more complex
   - Manual paste: Simple, explicit, easier to debug

2. **How to handle large outputs** (videos)?
   - Base64 in response (simple, limited by API size)
   - S3 upload (more complex, better for large files)

3. **Progress updates**: Real-time or polling?
   - WebSocket for live updates (complex)
   - Status polling every 3 seconds (simple)

4. **Error recovery**: Retry logic?
   - Automatic retry with exponential backoff
   - Or fail fast and let user retry manually

5. **Multi-endpoint support**: Single endpoint or multiple?
   - Multiple endpoints for different GPU types
   - Or single endpoint with auto-routing

---

## Next Steps

1. **Set up development environment**
   - Install ComfyUI locally
   - Create RunPod account and serverless endpoint
   - Configure Network Volume with models

2. **Implement MVP**
   - Basic node structure
   - API communication (submit + poll)
   - Image encoding/decoding
   - Error handling

3. **Test thoroughly**
   - Unit tests for image conversion
   - Integration test with RunPod API
   - Manual testing with various workflows

4. **Document**
   - README with installation instructions
   - Usage examples
   - Troubleshooting guide

5. **Release**
   - Publish to GitHub
   - Submit to ComfyUI Manager registry
   - Share with community

---

**End of Context Document**

This document should provide comprehensive context for implementing the ComfyUI RunPod remote execution custom node. All architectural decisions, security requirements, and implementation details are documented for reference during development.
