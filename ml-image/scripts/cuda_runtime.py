"""Options CUDA isolées par film ; aucun appel CUDA sur le parcours CPU."""
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar

import torch
from loguru import logger

_AMP_ENABLED = ContextVar('ric_cuda_amp', default=False)


def is_cuda(device):
    return torch.device(device).type == 'cuda'


def autocast_context(device):
    # Compatible avec le profil local PyTorch 2.2.
    if is_cuda(device) and _AMP_ENABLED.get():
        return torch.autocast(device_type='cuda', dtype=torch.float16)
    return nullcontext()


@contextmanager
def inference_options(device, amp=False, profile_memory=False, clear_cache=False):
    """Mesurer les pics par film et restaurer les options même après erreur."""
    device = torch.device(device)
    token = _AMP_ENABLED.set(bool(amp) and is_cuda(device))
    try:
        if is_cuda(device) and profile_memory:
            torch.cuda.synchronize(device)
            torch.cuda.reset_peak_memory_stats(device)
        yield
    finally:
        _AMP_ENABLED.reset(token)
        if is_cuda(device):
            if profile_memory:
                torch.cuda.synchronize(device)
                logger.info(
                    'CUDA {} : allouée={:.1f} Mio, réservée={:.1f} Mio, '
                    'pic alloué={:.1f} Mio, pic réservé={:.1f} Mio',
                    device, torch.cuda.memory_allocated(device) / 1024**2,
                    torch.cuda.memory_reserved(device) / 1024**2,
                    torch.cuda.max_memory_allocated(device) / 1024**2,
                    torch.cuda.max_memory_reserved(device) / 1024**2,
                )
            if clear_cache:
                with torch.cuda.device(device):
                    torch.cuda.empty_cache()
