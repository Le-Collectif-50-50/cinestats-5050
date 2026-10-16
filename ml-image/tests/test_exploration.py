"""Contrats d'exploration, sans modèles ni téléchargement."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import pandas as pd
import torch
from scripts import filter_detections as filters, pipelines, vision_detection


class ExplorationTests(unittest.TestCase):
    def test_crops_preserve_boxes_and_unique_ids(self):
        detector = object.__new__(vision_detection.VisionDetection)
        detector.H_resized = detector.W_resized = 100
        box = SimpleNamespace(xyxy=[[10, 10, 50, 50]], conf=torch.tensor(.9))
        detector.get_areas_of_interest = lambda *a, **k: [SimpleNamespace(boxes=[box])] * 2
        frames = np.zeros((2, 100, 100, 3), dtype=np.uint8)
        old = detector.crop_areas_of_interest(123, frames, 100, 100)
        new = detector.crop_areas_of_interest(123, frames, 100, 100, bbox_expand_factor=.5)
        self.assertEqual([d['perso_id'] for d in new], [0, 1])
        for before, after in zip(old, new, strict=False):
            self.assertEqual(after['movie_id'], 123)
            self.assertEqual(after['bbox'], before['bbox'])
            self.assertEqual(after['crop_bbox'], [0, 0, 70, 70])
            self.assertEqual(after['cropped_face'].shape, (70, 70, 3))
            self.assertEqual(filters.compute_area(before['bbox'], 10000), filters.compute_area(after['bbox'], 10000))
        for factor in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                detector.crop_areas_of_interest(123, frames, 100, 100, bbox_expand_factor=factor)

    def test_overlap_optional_ordered_and_frame_local(self):
        detections = [dict(perso_id=i, frame_id=frame, bbox=box, conf=.9)
                      for i, (frame, box) in enumerate([(0, [1, 1, 9, 9]), (1, [1, 1, 9, 9]), (0, [0, 0, 10, 10])])]
        self.assertEqual(len(filters.filter_detections_clustering(detections, 100, 0, 1, 0)), 3)
        with patch.object(filters.evaluation_annotation, 'register_faces_intermediate_results') as register:
            selected = filters.filter_detections_clustering(detections, 100, 0, 1, 0, mode='eval', remove_overlaps=True)
        self.assertEqual([d['perso_id'] for d in selected], [1, 2])
        self.assertEqual([d['perso_id'] for d in register.call_args.args[1]], [0])
        self.assertEqual(filters.compute_iou([0, 0, 0, 0], [0, 0, 0, 0]), 0)
        self.assertEqual(filters.remove_overlapping_faces_per_frame([]), [])

    def test_device_and_options(self):
        with patch.object(torch.cuda, 'is_available', return_value=False):
            self.assertEqual(str(pipelines.resolve_device('auto')), 'cpu')
            with self.assertRaises(ValueError):
                pipelines.resolve_device('cuda')
        with patch.object(torch.cuda, 'is_available', return_value=True):
            self.assertEqual(str(pipelines.resolve_device('cpu')), 'cpu')
            self.assertEqual(str(pipelines.resolve_device('auto')), 'cuda')
        for args in [SimpleNamespace(device='bogus'), SimpleNamespace(bbox_expand_factor=-.1), SimpleNamespace(iou_threshold=1.1)]:
            with self.assertRaises(ValueError):
                pipelines.exploration_options(args)

    def test_batch_modes_forward_options(self):
        args = SimpleNamespace(column_identifier='visa_number', num_cpu=1, batch_size=2,
                               min_area=0, max_area=1, min_conf=0, min_conf_cla=0,
                               min_sharpness_cla=0, max_z_cla=0, min_mouth_opening_cla=0,
                               cluster_model='chinese_whispers', cluster_threshold=.92,
                               agr_method='majority', store_visuals=False, istart=0, istop=1,
                               source='test.csv', device='cpu', bbox_expand_factor=.3,
                               remove_overlaps=True, iou_threshold=.7)
        paths = dict(dl_media='media', all_results='results', temp_preds='preds', final_preds='final')
        for runner in [pipelines.infer_pipeline, pipelines.evaluate_pipeline]:
            with patch.object(pipelines, 'predict_one_item', side_effect=RuntimeError('test')) as predict, patch.object(pipelines.utils, 'gather_and_save_predictions'):
                runner(args, pd.DataFrame([dict(visa_number=1)]), paths)
            self.assertEqual(predict.call_args.kwargs['device_arg'], 'cpu')
            self.assertEqual(predict.call_args.kwargs['bbox_expand_factor'], .3)
            self.assertTrue(predict.call_args.kwargs['remove_overlaps'])
            self.assertEqual(predict.call_args.kwargs['iou_threshold'], .7)

    def test_item_preserves_poster_embedding_ids(self):
        kwargs = dict(column_identifier='visa_number', num_cpu=1, batch_size=2,
                      min_area=0, max_area=1, min_conf=0, min_conf_cla=0,
                      min_sharpness_cla=0, max_z_cla=0, min_mouth_opening_cla=0,
                      cluster_model='chinese_whispers', cluster_threshold=.92,
                      agr_method='majority', store_visuals=False, downloaded_media_path='media',
                      poster_path='poster', trailer_path='trailer', row={'visa_number': 1},
                      device_arg='cpu', bbox_expand_factor=.3, remove_overlaps=True)
        with patch.object(pipelines.utils, 'load_data_from_links', return_value=({'image': np.zeros((2, 2, 3)), 'trailer_path': 'trailer'}, 'url')), patch.object(pipelines, 'infer_on_trailer', return_value=([], np.zeros((1, 512)), [42])) as trailer, patch.object(pipelines, 'infer_on_poster', return_value=[]) as poster:
            pipelines.predict_one_item(**kwargs)
        self.assertEqual(trailer.call_args.kwargs['bbox_expand_factor'], .3)
        self.assertTrue(trailer.call_args.kwargs['remove_overlaps'])
        self.assertEqual(poster.call_args.kwargs['bbox_expand_factor'], .3)
        self.assertEqual(poster.call_args.args[2], [42])
        self.assertEqual(str(poster.call_args.args[8]), 'cpu')
