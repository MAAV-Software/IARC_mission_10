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

    model = YOLO('yolo11n.pt') 

    print("Starting Detection Training...")
    results = model.train(
        data='iarc_dataset/data.yaml', 
        device=device_id,
        epochs=300,        
        patience=50,       
        batch=16,          
        imgsz=640,         
        
        hsv_h=0.04,        
        hsv_s=0.6,         
        hsv_v=0.4,         
        degrees=180,       
        flipud=0.5,        
        fliplr=0.5,        
        mosaic=1.0,        
        
        project='iarc_mission',
        name='green_mine_detect_v1',
        exist_ok=True      
    )
    print(f"Training Complete.")