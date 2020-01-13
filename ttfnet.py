# model settings
from pathlib import Path
model = dict(
    type='AugmixTTFNet',
    pretrained='/mnt/nfs/Other/pytorch_pretrained_backbones/vovnet39/vovnet39__21_12_19__04_37_39.pth',
    backbone=dict(
        type='VoVNet39',
        pretrained=False,
        out_indices=(1, 2, 3, 4)),
    neck=dict(
        type='BIFPN',
        in_channels=[256, 512, 768, 1024],
        num_outs=4,
        out_channels=256
    ),
    bbox_head=dict(
        type='TTFHead',
        build_neck=True,
        inplanes=[256, 256, 256, 256],
        head_conv=128,
        wh_conv=64,
        hm_head_conv_num=2,
        wh_head_conv_num=1,
        num_classes=6,
        wh_offset_base=16,
        wh_agnostic=True,
        wh_gaussian=True,
        norm_cfg=dict(type='BN'),
        alpha=0.54,
        hm_weight=1.,
        wh_weight=5.,
        max_objs=256,
        receptive_field_layer='conv'))
cudnn_benchmark = True
# training and testing settings
train_cfg = dict(
    vis_every_n_iters=100,
    debug=True,
    # distillation=dict(
    #     backbone_levels=[
    #         dict(idx=0, student_sigmoid=True, teacher_sigmoid=True, coeff=1., loss='js_div'),
    #         dict(idx=1, student_sigmoid=True, teacher_sigmoid=True, coeff=1., loss='js_div'),
    #         dict(idx=2, student_sigmoid=True, teacher_sigmoid=True, coeff=1., loss='js_div'),
    #         dict(idx=3, student_sigmoid=True, teacher_sigmoid=True, coeff=1., loss='js_div')
    #     ],
    #     head_levels=[
    #         dict(idx=0, student_sigmoid=False, teacher_sigmoid=True, coeff=1., loss='js_div'),
    #         dict(idx=1, student_sigmoid=True, teacher_sigmoid=True, coeff=1., loss='js_div'),
    #     ]
    # )
)
test_cfg = dict(
    score_thr=0.01,
    max_per_img=256)
# dataset settings
albu_train_transforms = [
    dict(type='HorizontalFlip'),
    dict(type='ShiftScaleRotate',
         shift_limit=[-0.01, 0.01],
         scale_limit=[-0.01, 0.01],
         rotate_limit=[-5, 5],
         border_mode=0,
         value=[128, 128, 128],
         p=0.5),
    dict(type='RandomBrightnessContrast',
         brightness_limit=[-0.2, 0.2],
         contrast_limit=[-0.2, 0.2],
         p=0.2),
    dict(type='OneOf',
         transforms=[
             dict(type='RGBShift', r_shift_limit=20, g_shift_limit=20, b_shift_limit=20, p=1.0),
             dict(type='HueSaturationValue', hue_shift_limit=10, sat_shift_limit=15, val_shift_limit=10, p=1.0)
         ], p=0.2),
    dict(type='JpegCompression', quality_lower=50, quality_upper=100, p=0.2),
    dict(type='CLAHE', p=0.3),
    dict(type='ToGray', p=0.1),
    dict(type='Cutout', num_holes=5, max_h_size=5, max_w_size=5, fill_value=[128, 128, 128])
]
width, height = 192, 128
albu_center_crop_pad = [
    dict(type='RandomResizedCrop', height=height, width=width, scale=(0.9, 1.)),
    dict(type='PadIfNeeded', min_height=height,
         min_width=width, border_mode=0, value=[128, 128, 128]),
]
dataset_type = 'DsslDataset'
img_norm_cfg = dict(
    mean=[0., 0., 0.], std=[255., 255., 255.], to_rgb=True)
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='Resize', img_scale=(256, 256), keep_ratio=True),
    dict(type='RandomFlip', flip_ratio=0.),
    dict(type='Albu',
         transforms=albu_center_crop_pad,
         bbox_params=dict(
             type='BboxParams',
             format='pascal_voc',
             label_fields=['gt_labels'],
             min_area=0.08,
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
    dict(type='Collect', keys=['img', 'img_augmix_0', 'img_augmix_1', 'gt_bboxes', 'gt_labels']),
]
width, height = 192, 128
test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(width, height),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Pad', size_divisor=32, pad_val=128),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img']),
        ])
]
data = dict(
    imgs_per_gpu=4,
    workers_per_gpu=8,
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
optimizer = dict(type='SGD', lr=0.00001, momentum=0.9, weight_decay=0.0004,
                 paramwise_options=dict(bias_lr_mult=2., bias_decay_mult=0.))
optimizer_config = dict(grad_clip=dict(max_norm=35, norm_type=2))
# learning policy
lr_config = dict(
    policy='torch',
    torch_scheduler='OneCycleLR',
    max_lr=0.02)
checkpoint_config = dict(interval=4)
# runtime settings
total_epochs = 140
device_ids = range(8)
dist_params = dict(backend='nccl')
log_level = 'INFO'
work_dir = './work_dirs/ttfnet'
load_from = './work_dirs/ttfnet/pretrained.pth'
resume_from = None
workflow = [('train', 1)]
log_config = dict(
    interval=30,
    hooks=[
        dict(type='TextLoggerHook'),
        # dict(type='WandbLoggerHook', project='lpr5_vehicle', config_filename=Path.absolute(Path(__file__)))
    ])

width, height = 192, 128
# extra_hooks = [
#     dict(type='KnowledgeDistillationHook',
#          # image_meta_to_update='plain',
#          teacher_model_config=dict(
#              type='AugmixTTFNet',
#              pretrained=None,
#              backbone=dict(
#                  type='VoVNet27Slim',
#                  out_indices=(1, 2, 3, 4)),
#              neck=None,
#              bbox_head=dict(
#                  type='TTFHead',
#                  build_neck=True,
#                  inplanes=[128, 256, 384, 512],
#                  head_conv=128,
#                  wh_conv=64,
#                  hm_head_conv_num=2,
#                  wh_head_conv_num=1,
#                  num_classes=6,
#                  wh_offset_base=16,
#                  wh_agnostic=True,
#                  wh_gaussian=True,
#                  norm_cfg=dict(type='BN'),
#                  alpha=0.54,
#                  hm_weight=1.,
#                  wh_weight=5.,
#                  max_objs=256,
#                  receptive_field_layer='conv')),
#          test_cfg=dict(
#              score_thr=0.3,
#              max_per_img=256),
#          test_pipeline=[
#              dict(type='LoadImageFromFile'),
#              dict(type='Resize', img_scale=(width, height), keep_ratio=True),
#              dict(type='RandomFlip', flip_ratio=0.),
#              dict(type='Albu',
#                   transforms=[
#                       dict(type='PadIfNeeded', min_height=max(width, height),
#                            min_width=max(width, height), border_mode=0, value=[128, 128, 128]),
#                       dict(type='CenterCrop', height=height, width=width)
#                   ],
#                   update_pad_shape=True,
#                   keymap={'img': 'image'}),
#              dict(type='Normalize', **img_norm_cfg),
#              dict(type='DefaultFormatBundle'),
#              dict(type='Collect', keys=['img']),
#          ],
#          model_checkpoint_path=Path('./work_dirs/ttfnet/best.pth')),
# ]
