import glob
from PIL import Image
from tqdm import tqdm, trange
import pdb

def merge_images_horizontally(image1_path, image2_path, output_path):
    # 打開兩張圖片
    
    name = image1_path.lower().split('/')[::-1][0]         # 將檔名換成小寫 ( 避免 JPG 與 jpg 干擾 )
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)
    #pdb.set_trace()
    # 確保兩張圖片尺寸相同
    if image1.size != image2.size:
        raise ValueError("兩張圖片尺寸不同，無法合併。")

    # 計算合併後的圖片寬度
    total_width = image1.width + image2.width

    # 創建新的圖片
    merged_image = Image.new("RGB", (total_width, image1.height))

    # 複製圖片到新圖片
    merged_image.paste(image1, (0, 0))
    merged_image.paste(image2, (image1.width, 0))

    # 儲存合併後的圖片
    merged_image.save(output_path+name)

if __name__ == '__main__':
# 路徑設置
    image_derain_path = glob.glob('./img_output/derain_ret/*.png')
    image2_src_path = glob.glob('./img_output/src/*.png')
    output_path = "./img_merge/"
    progress = tqdm(total=len(image_derain_path))
    for image1_path, image2_path in zip(image_derain_path , image2_src_path):
    # 呼叫函數合併圖片
        merge_images_horizontally(image1_path, image2_path, output_path)
        progress.update(1)