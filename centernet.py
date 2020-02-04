# model settings
from pathlib import Path
model = dict(
    type='AugmixCenterNet',
    pretrained='/mnt/nfs/Other/pytorch_pretrained_backbones/vovnet27_slim/vovnet27_slim__21_12_19__02_07_52.pth',
    backbone=dict(
        type='VoVNet27Slim',
        activation='relu',
        out_indices=(1, 2, 3, 4)),
    neck=None,
    bbox_head=dict(
        type='CenternetDetectionHead',
        require_upsampling=True,
        inplanes=(128, 256, 384, 512),
        planes=(256, 128, 64),
        base_down_ratio=32,
        hm_head_conv=128,
        hm_offset_heads_conv=128,
        wh_heads_conv=128,
        with_deformable=False,
        hm_head_conv_num=2,
        hm_offset_head_conv_num=2,
        wh_head_conv_num=2,
        num_classes=6,
        shortcut_kernel=3,
        norm_cfg=dict(type='BN'),
        shortcut_cfg=(1, 2, 3),
        num_stacks=1,  # It can be > 1 in backbones such as hourglass
        ellipse_gaussian=True,
        exp_wh=False,
        hm_weight=1.,
        hm_offset_weight=1.,
        wh_weight=0.1,
        max_objs=512))
cudnn_benchmark = True
# training and testing settings
train_cfg = dict(
    vis_every_n_iters=100,
    debug=False,
)
test_cfg = dict(
    score_thr=0.01,
    max_per_img=32)
# dataset settings
width, height = 128, 96
albu_center_crop_pad = [
    dict(type='ToGray', p=0.2),
    dict(type='JpegCompression', quality_lower=50, quality_upper=100,),
    dict(type='PadIfNeeded', min_height=height, min_width=width, border_mode=0, value=[128, 128, 128]),
    dict(type='ShiftScaleRotate', rotate_limit=(-0., 0.), scale_limit=(-0.02, 0.3), shift_limit=0.,
         border_mode=0, value=[128, 128, 128]),
]
dataset_type = 'DsslDataset'
img_norm_cfg = dict(
    mean=[0., 0., 0.], std=[255., 255., 255.], to_rgb=True)
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='ResizeWithKeepAspectRatio', max_width=width, max_height=height),
    dict(type='RandomFlip', flip_ratio=0.5),
    dict(type='Albu',
         filter_invalid_bboxes=True,
         transforms=albu_center_crop_pad,
         bbox_params=dict(
             type='BboxParams',
             format='pascal_voc',
             label_fields=['gt_labels'],
             min_area=0.5,
             min_visibility=0.1,
             filter_lost_elements=True),
         update_pad_shape=True,
         keymap={
             'img': 'image',
             'gt_bboxes': 'bboxes'
         }),
    dict(type='AugMix', with_js_loss=True),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img',
                               'img_augmix_0', 'img_augmix_1',
                               'gt_bboxes', 'gt_labels']),
]
width, height = 128, 96
test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(width, height),
        flip=False,
        transforms=[
            dict(type='Resize', img_scale=(width, height), keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Pad', size_divisor=32, pad_val=128),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img']),
        ])
]
data = dict(
    imgs_per_gpu=32,
    workers_per_gpu=16,
    train=dict(
        type=dataset_type,
        ann_file='./data_loader.py',
        load_and_dump_config_name='train_load_config',
        composer_config_name='train_composer_config',
        pipeline=train_pipeline),
    val=dict(
        type=dataset_type,
        ann_file='./data_loader.py',
        load_and_dump_config_name='test_load_config',
        composer_config_name='test_composer_config',
        pipeline=test_pipeline),
    test=dict(
        type=dataset_type,
        ann_file='./data_loader.py',
        load_and_dump_config_name='test_load_config',
        composer_config_name='test_composer_config',
        pipeline=test_pipeline))
# optimizer
optimizer = dict(type='SGD', lr=0.002, momentum=0.9, weight_decay=0.0004,
                 paramwise_options=dict(bias_lr_mult=2., bias_decay_mult=0.))
optimizer_config = dict(grad_clip=dict(max_norm=35, norm_type=2))
# learning policy
lr_config = dict(
    policy='torch',
    torch_scheduler='OneCycleLR',
    max_lr=0.02)
checkpoint_config = dict(interval=4)
# runtime settings
total_epochs = 200
device_ids = range(8)
dist_params = dict(backend='nccl')
log_level = 'INFO'
work_dir = './work_dirs/centernet'
load_from = None
resume_from = None
workflow = [('train', 1)]
log_config = dict(
    interval=30,
    hooks=[
        dict(type='TextLoggerHook'),
        dict(type='WandbLoggerHook', project='lpr5_vehicle', config_filename=Path.absolute(Path(__file__)))
    ])
