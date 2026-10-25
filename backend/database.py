import os
import pandas as pd

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets')

def load_project_datasets():
    """Fully loads and integrates DLdataset1, DLdataset2, and DLdataset3 using Pandas."""
    dataset_records = []
    
    try:
        # 1. Load DLdataset1 (Categories & Template Guidelines)
        path1 = os.path.join(DATASET_DIR, 'DLdataset1.xlsx')
        if os.path.exists(path1):
            df1 = pd.read_excel(path1, sheet_name='Dataset Template')
            print(f"Loaded Dataset 1 (Templates): {df1.shape[0]} rows")

        # 2. Load DLdataset2 (Image Metadata & Paths)
        path2 = os.path.join(DATASET_DIR, 'DLdataset2.csv')
        image_mapping = {}
        if os.path.exists(path2):
            df2 = pd.read_csv(path2)
            print(f"Loaded Dataset 2 (Images): {df2.shape[0]} rows")
            for _, row in df2.iterrows():
                filename = str(row.get('image_filename', ''))
                folder_path = str(row.get('image_folder_path', ''))
                if filename:
                    image_mapping[filename] = folder_path

        # 3. Load DLdataset3 (Incident Reports & Match Group IDs)
        path3 = os.path.join(DATASET_DIR, 'DLdataset3.xlsx')
        if os.path.exists(path3):
            df3 = pd.read_excel(path3, sheet_name='Sheet1')
            print(f"Loaded Dataset 3 (Incidents): {df3.shape[0]} rows")
            
            for _, row in df3.iterrows():
                img_name = str(row.get('image_filename', ''))
                img_url = f"http://127.0.0.1:5000/uploads/{img_name}" if img_name in image_mapping else None

                dataset_records.append({
                    "id": str(row.get('report_id', 'R001')),
                    "report_type": str(row.get('report_type', 'lost')).lower(),
                    "item_name": str(row.get('item_category', 'Item')),
                    "item_category": str(row.get('item_category', 'General')),
                    "colour": str(row.get('colour', 'Unknown')),
                    "brand": str(row.get('brand', 'Unknown')),
                    "description": str(row.get('description', '')),
                    "location": str(row.get('location', 'Campus')),
                    "reporter_email": f"{row.get('reporter_user_id', 'U001')}@campus.edu",
                    "reporter_role": str(row.get('reporter_role', 'Student')),
                    "user_token": f"Token_{row.get('reporter_user_id', 'U001')}",
                    "image_url": img_url,
                    "feature_vector": None,
                    "match_group_id": str(row.get('match_group_id', ''))
                })

        print(f"Successfully processed total {len(dataset_records)} records from datasets.")
    except Exception as e:
        print(f"Dataset loading notice: {e}")
        
    return dataset_records