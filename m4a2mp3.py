"""
1. 新規購入したファイルをfrom4aフォルダにコピー(フォルダ内は再帰的に探索される)
2. tomp3フォルダの中身が空になっていることを確認する
3. moraフォルダ内で python m4a2mp3.py を実行
4. from4aの中身を空にする
"""
import os
import sys
import io
import pathlib
from mutagen.mp4 import MP4
from PIL import Image
from io import BytesIO

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def get_file_name(path) :
    """
    ファイルパスからファイル名だけを取得
    ex) from4a/hoge.m4a → hoge
    """
    return os.path.splitext(os.path.basename(path))[0]

def replace_invalidchar(s, replace='@'):
    """
    windowsのファイルシステムで使用不可能な文字を置き換える
    """
    return (
        s.replace('"', replace)
            .replace('<', replace)
            .replace('>', replace)
            .replace('|', replace)
            .replace(':', replace)
            .replace('*', replace)
            .replace('?', replace)
            .replace('\\', replace)
            .replace('/', replace)
    )

# 出力前後のディレクトリ
from_dir = "from4a"
to_dir = "tomp3"


# 同一のアルバムでは同じアルバムアートを使用している前提とし、
# 同じアルバムアートを何度も生成しなくてもいいようにパスを保存しておくための変数
dict = {}

# アルバムアートを付ける前のmp3ファイルを配置するテンポラリーディレクトリがなければ作成
if(not os.path.exists('{}/tmp'.format(to_dir))):
    os.makedirs('{}/tmp'.format(to_dir))


# .m4a→.mp3
# from4aにあるディレクトリを再帰的に探索し、
# *.m4aのデータをtomp3ディレクトリへmp3として保存する
p = pathlib.Path(from_dir)
for file_path in p.glob( '**/*.m4a'):
    try:
        print(file_path)

        file_name = get_file_name(file_path)
        mp4 = MP4(file_path)

        # ファイル情報から必要なものを取得する
        # track_title     = mp4.tags["\xa9nam"][0]
        album           = mp4.tags["\xa9alb"][0]
        artist          = mp4.tags["\xa9ART"][0]
        cover           = mp4.tags["covr"][0]
        # year            = mp4.tags["\xa9day"][0]
        # bitrate         = mp4.info.bitrate
        # length          = mp4.info.length
        # channels        = mp4.info.channels
        # sample_rate     = mp4.info.sample_rate
        # bits_per_sample = mp4.info.bits_per_sample
        # codec           = mp4.info.codec

        # アートワークを付ける前のmp3名
        tmp_mp3_file_name = '{}/tmp/{}.mp3'.format(to_dir, file_name)
        if(os.path.exists(tmp_mp3_file_name)):
            # 既に同名のmp3ファイルがある場合はファイル名の後ろに-アーティスト名をつける
            file_name = '{}/tmp/{}-{}.mp3'.format(to_dir, file_name, artist)

        image_name = ''
        if(album not in dict):
            # 初登場のアルバムのときはアルバム名をjpgのファイル名としてアートワークを生成し、
            # tomp3ディレクトリに保存する
            image = Image.open(BytesIO(cover))
            image_name = album
            image_name = replace_invalidchar(image_name)
            image_name = '{}/{}.jpg'.format(to_dir, image_name)
            image.save(image_name)
            dict[album] = image_name
        else:
            # 一度登場したアルバムのときは同じアートワークを使用する
            image_name = dict[album]

        # m4aをmp3(アートワークなし)に変換する
        os.system('ffmpeg -i "{}" -ab 256k "{}"'
            .format(file_path, tmp_mp3_file_name))

        # mp3(アートワークなし)にアートワークをつける
        withart_mp3_file_name = "{}/{}.mp3".format(to_dir, file_name)
        os.system('ffmpeg -y -i "{}" -i "{}" -ab 256k -map 0:a -map 1:v -c copy -disposition:1 attached_pic -id3v2_version 3 -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" "{}"'
            .format(tmp_mp3_file_name, image_name, withart_mp3_file_name))

        # mp3(アートワークなし)を削除する
        os.remove(tmp_mp3_file_name)
    except Exception as e:
        print(e)
