import torch
from ultralytics import YOLO

def check_cuda():
    print("-" * 30)
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        return 0 
    else:
        return 'cpu'

if __name__ == '__main__':
    device_id = check_cuda()

    model = YOLO('./weights/12-2-25.pt')

    print("Starting Detection Training...")
    results = model.train(
        data="./dataset/data.yaml",
        device=device_id,
        epochs=30,        
        patience=50,       
        batch=32,          
        imgsz=256,         
        
        hsv_h=0.04,        
        hsv_s=0.6,         
        hsv_v=0.4,         
        degrees=180,       
        flipud=0.5,        
        fliplr=0.5,        
        mosaic=1.0,        
        
        project="./training_output",
        name='green_mine_detect_v1',
        exist_ok=True      
    )
    print(f"Training Complete.")