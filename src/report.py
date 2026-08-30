import os
import glob
import re
import subprocess
import boto3

def get_s3_client():
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )

def export_and_upload_reports():
    stages = ["1_understanding", "3_modeling", "4_evaluation"]
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    bucket = os.environ.get("R2_BUCKET", "kopdes")
    public_url = os.environ.get("R2_PUBLIC_URL") or f"https://{account_id}.r2.cloudflarestorage.com/{bucket}"
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    s3 = get_s3_client()

    for stage in stages:
        ipynb_file = f"src/outs/{stage}.ipynb"
        if not os.path.exists(ipynb_file):
            print(f"[SKIP] Notebook not found: {ipynb_file}")
            continue

        print(f"[CONVERT] Converting {ipynb_file} to Markdown...")
        subprocess.run(
            ["jupyter", "nbconvert", "--to", "markdown", "--no-input", ipynb_file, "--output-dir", "src/outs"],
            check=True
        )

        md_file = f"src/outs/{stage}.md"
        if not os.path.exists(md_file):
            continue

        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        images = glob.glob(f"src/outs/{stage}_files/*.png")
        for img_path in images:
            filename = os.path.basename(img_path)
            key = f"reports/{filename}"
            print(f"[UPLOAD] Uploading {img_path} -> s3://{bucket}/{key}")
            s3.upload_file(
                img_path,
                bucket,
                key,
                ExtraArgs={"ContentType": "image/png"}
            )
            image_url = f"{public_url}/{key}"

            # Replace markdown image syntax ![alt](path) with HTML <img> tag
            img_pattern = rf'!\[(.*?)\]\({re.escape(f"{stage}_files/{filename}")}\)'
            img_tag = f'<img src="{image_url}" alt="{filename}" />'
            content = re.sub(img_pattern, img_tag, content)

            # Fallback for any other remaining relative path references
            content = content.replace(f"{stage}_files/{filename}", image_url)

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)

        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(content + "\n\n")

if __name__ == "__main__":
    export_and_upload_reports()
