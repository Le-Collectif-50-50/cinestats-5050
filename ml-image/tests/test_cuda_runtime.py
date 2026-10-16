"""Contrats CPU et CUDA simulé ; test matériel conditionnel."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import numpy as np
import torch
from scripts import cuda_runtime, pipelines, faces_clustering, vision_classifiers, vision_detection


class CudaRuntimeTests(unittest.TestCase):
    def test_cpu_never_calls_cuda(self):
        with patch.object(torch, 'cuda') as cuda, patch.object(torch, 'autocast') as autocast:
            with cuda_runtime.inference_options('cpu', amp=True, profile_memory=True, clear_cache=True):
                with cuda_runtime.autocast_context('cpu'):
                    pass
            self.assertEqual(cuda.mock_calls, [])
            autocast.assert_not_called()

    def test_cleanup_and_restoration_after_failure(self):
        with patch.object(torch, 'cuda') as cuda, patch.object(torch, 'autocast') as autocast, patch.object(cuda_runtime.logger, 'info'):
            with self.assertRaisesRegex(RuntimeError, 'failure'):
                with cuda_runtime.inference_options('cuda:1', amp=True, profile_memory=True, clear_cache=True):
                    with cuda_runtime.autocast_context('cuda:1'):
                        raise RuntimeError('failure')
            autocast.assert_called_once_with(device_type='cuda', dtype=torch.float16)
            cuda.reset_peak_memory_stats.assert_called_once_with(torch.device('cuda:1'))
            cuda.max_memory_allocated.assert_called_once_with(torch.device('cuda:1'))
            cuda.device.assert_called_once_with(torch.device('cuda:1'))
            cuda.empty_cache.assert_called_once()
            autocast.reset_mock()
            with cuda_runtime.autocast_context('cuda'):
                pass
            autocast.assert_not_called()

    def test_pipeline_options_forwarded(self):
        args = SimpleNamespace(cuda_amp=True, profile_memory=True, clear_cuda_cache=True)
        with patch.object(torch.cuda, 'is_available', return_value=False), patch.object(cuda_runtime, 'inference_options') as options, patch.object(pipelines, 'predict_one_item', return_value=([], [])) as predict:
            self.assertEqual(pipelines.predict_with_cuda_options(args, 'value', mode='eval'), ([], []))
        options.assert_called_once_with(torch.device('cpu'), amp=True, profile_memory=True, clear_cache=True)
        predict.assert_called_once_with('value', mode='eval')

    def test_embedding_fp32_output(self):
        model = object.__new__(faces_clustering.EmbeddingModel)
        model.device, model.model_name = torch.device('cpu'), 'facenet'
        model.model = lambda batch: torch.ones((len(batch), 512), dtype=torch.float16)
        with patch.object(faces_clustering, 'DataLoader', return_value=[torch.zeros((2, 3, 160, 160))]) as loader:
            result = model.get_embedding(2, [])
        self.assertFalse(loader.call_args.kwargs['pin_memory'])
        self.assertEqual(result.shape, (2, 512))
        self.assertEqual(result.dtype, np.float32)

    def test_classifier_fp32_probabilities(self):
        model = object.__new__(vision_classifiers.VisionClassifier)
        model.device = torch.device('cpu')
        model.model_fair_7 = lambda batch: torch.arange(18, dtype=torch.float16).repeat(len(batch), 1)
        with patch.object(vision_classifiers, 'DataLoader', return_value=[torch.zeros((2, 3, 224, 224))]), patch.object(torch, 'softmax', wraps=torch.softmax) as softmax:
            result = model.predict_age_gender_ethnicity([], expose_confs=True)
        self.assertEqual(len(result[0]), 2)
        for call in softmax.call_args_list:
            self.assertEqual(call.args[0].dtype, torch.float32)
        for probabilities in result[3:]:
            self.assertAlmostEqual(sum(probabilities[0]), 1, places=6)

    def test_detection_results_evacuated_per_batch(self):
        model = object.__new__(vision_detection.VisionDetection)
        model.device = torch.device('cpu')
        model.H_resized = model.W_resized = 16
        results = [MagicMock(), MagicMock()]
        model.yolo_model_face = MagicMock(side_effect=[[results[0]], [results[1]]])
        with patch.object(vision_detection, 'DataLoader', return_value=[torch.zeros((1, 3, 16, 16))] * 2):
            actual = model.get_areas_of_interest(np.zeros((2, 16, 16, 3), dtype=np.uint8))
        self.assertEqual(actual, [r.cpu.return_value for r in results])
        for result in results:
            result.cpu.assert_called_once()

    @unittest.skipUnless(torch.cuda.is_available(), 'CUDA indisponible')
    def test_real_cuda_amp(self):
        model = torch.nn.Linear(8, 4).cuda().eval()
        batch = torch.ones((2, 8), device='cuda')
        with torch.no_grad(), cuda_runtime.inference_options('cuda', amp=True, profile_memory=True, clear_cache=True):
            with cuda_runtime.autocast_context('cuda'):
                output = model(batch)
            self.assertEqual(output.dtype, torch.float16)
            self.assertTrue(torch.isfinite(output).all())
        with cuda_runtime.autocast_context('cuda'):
            self.assertEqual(model(batch).dtype, torch.float32)
