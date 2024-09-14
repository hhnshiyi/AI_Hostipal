import subprocess

# 格式转换
def convert_audio(input_file, output_file):
    command = [
        'ffmpeg',
        '-i', input_file,
        '-vn',  # 不包含视频流
        '-ar', '44100',  # 设置采样率
        '-ac', '2',  # 设置声道数
        '-ab', '192k',  # 设置比特率
        '-f', 'wav',  # 输出格式为wav
        output_file
    ]

    try:
        # 执行 FFmpeg 命令
        subprocess.run(command, check=True)
        print(f"转换成功：{input_file} -> {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"转换失败：{e}")


# 合并音频文件

def merge_audio_files(file1, file2, output_file, output_format='mp3'):
    # 构造 ffmpeg 命令
    command = [
        'ffmpeg',
        '-i', file1,
        '-i', file2,
        '-filter_complex', '[0:a][1:a]concat=n=2:v=0:a=1',
        '-b:a', '192k',
        '-f', output_format,  # 指定输出格式
        output_file
    ]

    # 执行命令
    try:
        subprocess.run(command, check=True)
        print(f"合并完成，输出文件为 {output_file}，格式为 {output_format}")
    except subprocess.CalledProcessError as e:
        print(f"执行 ffmpeg 出错: {e}")

# 使用函数
if __name__ == "__main__":
    # 转换
    # input_mp3 = r".mp3"
    # output_wav = r"audio_tes.wav"
    #
    # convert_audio(input_mp3, output_wav)
    # 合并
    file1 = 'output/1725859426.mp3'
    file2 = 'output/1725859431.mp3'
    output_file = 'combined_audio.wav'
    output_format = 'wav'  # 指定输出格式为 WAV
    merge_audio_files(file1, file2, output_file, output_format)