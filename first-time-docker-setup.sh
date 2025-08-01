cd d:\Projects\Co-DETR
docker build -t co-detr -f docker/Dockerfile .

docker run --gpus all -it --shm-size=8g -v d:\Projects\Co-DETR:/Co-DETR co-detr

pip install -v -e .

python demo/image_demo.py demo/demo.jpg projects/configs/co_dino_vit/co_dino_5scale_vit_large_coco.py pytorch_model.pth --score-thr 0.2 --out-file result.jpg

python demo/image_demo.py input_images/4616433--17.jpg projects/configs/co_dino_vit/co_dino_5scale_vit_large_coco.py pytorch_model.pth --score-thr 0.2 --out-file result_images/4616433--17_result.jpg

python demo/image_demo.py input_images/1726236152976.jpg projects/configs/co_dino_vit/co_dino_5scale_vit_large_coco.py pytorch_model.pth --score-thr 0.2 --out-file result_images/1726236152976_result.jpg