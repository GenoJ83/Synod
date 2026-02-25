from huggingface_hub import HfApi

api = HfApi()

print("Checking targeted datasets...")

def check_dataset(ds_id):
    try:
        info = api.dataset_info(ds_id)
        has_parquet = False
        if hasattr(info, 'siblings'):
            for sibling in info.siblings:
                if sibling.rfilename.endswith('.parquet') or "refs/convert/parquet" in sibling.rfilename:
                    has_parquet = True
                    break
        print(f"Dataset: {ds_id} | Has Parquet: {has_parquet}")
    except Exception as e:
        print(f"Error checking {ds_id}: {e}")

# Known scientific/keyword datasets
check_dataset("midas/inspec")
check_dataset("midas/kp20k")
check_dataset("midas/krapivin")
check_dataset("midas/nus")
check_dataset("midas/semeval2017")
check_dataset("thoppy/science_keyword_extraction")

