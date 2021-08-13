import os
import configparser
import requests
from bs4 import BeautifulSoup

def read_settings():
	"""
	settings.iniを読み込みます
	"""
	try:
		ini = configparser.ConfigParser()
		ini.read("settings.ini", encoding="utf-8_sig")
		writers_ = ini["writers"]["idlist"]
		writers = []
		for i in writers_.split(","):
			if i:
				writers.append(i)
	except Exception as e:
		print(f"{e}\nsettings.ini読み込みエラーだよ～ちゃんと用意してね～")
		exit()
	
	return writers

def get_download_target_urls(writer_id) -> list:
	""" ライター固有のID（author_id）から、ダウンロード対象のページURLを取得し、リストで返します """
	download_target_urls = []

	for page_num in range(1, 999):
		request_url = f"https://am-our.com/author/{writer_id}/page/{page_num}/"
		response = requests.get(request_url)
		soup = BeautifulSoup(response.text,'lxml')
		pages = soup.select(".eyecatch__link eyecatch__link-mask-latest")

		if pages == []: # ページ遷移先がなくなった時
			break

		while pages:
			try:
				article = pages.pop()
				relative_url = article.get("href")
				url = f"https://cakes.mu{relative_url}"
				download_target_urls.append(url)
			except Exception as e:
				print(e)

	return download_target_urls

def get_series_info(article_url):
	"""個別記事urlから著者名とシリーズ名のみを取得"""

	response = requests.get(article_url)
	soup = BeautifulSoup(response.text,'lxml')

	author = soup.find("meta", attrs={"name": "author"})["content"] # 著者
	series_title = soup.select("#area_main .box-series .post-items .post-title a")[0].getText().rstrip() # シリーズ名

	return author, series_title

def download_images(article_url, series_num, cookie):
	"""個別ページのurlから画像をダウンロードします
	series_numは連載の中の何話目かを示す変数であるが、
	cakesは連載ごとにそのページが第何話なのか特定できるシリーズ番号を振っていない？のでこちらで管理する必要がある"""

	response = requests.get(article_url, cookies=cookie)
	soup = BeautifulSoup(response.text,'lxml')

	author = soup.find("meta", attrs={"name": "author"})["content"] # 著者
	series_title = soup.select("#area_main .box-series .post-items .post-title a")[0].getText().rstrip() # シリーズ名
	article_title = soup.select(".article-title")[0].getText().strip() # 記事名
	article_id = article_url.rsplit("/")[-1] # 記事ID

	print(f"★ {article_id=} {article_title} をダウンロードします")

	for idx, elm in enumerate(soup.select(".article-content p img")):
		url = elm.get("src")
		try:
			filename = f"{str(series_num)}_{article_title}({article_id})_{str(idx+1)}.png" # 現在はpng以外の拡張子を想定してない
			# dest = os.path.join(dirname, filename)
			response = requests.get(url)
			image = response.content
			with open(filename, mode="wb") as file:
				file.write(image)
		except Exception as e:
			print(e)

def main():
	print("★ starting am-eater...")
	root_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(root_dir)

	writers = read_settings()

	# シリーズの全記事urlの取得
	for writer_id in writers:
		download_target_urls = get_download_target_urls(writer_id)
		download_target_urls.sort()

		target = download_target_urls[0] # 第1話ページから著者名とシリーズ名を取得
		author, series_title = get_series_info(target)

		# ダウンロード先フォルダ作成と移動
		dest_dir = os.path.join(root_dir, author, series_title)
		os.makedirs(dest_dir, exist_ok=True)
		os.chdir(dest_dir)

		# downloaded.txtが存在しないなら作成する
		downloaded_txt = os.path.join(dest_dir, "downloaded.txt")
		if not os.path.isfile(downloaded_txt):
			with open(downloaded_txt, mode="w") as f:
				f.write("")
			
		# downloaded.txtの読み込み
		f = open(downloaded_txt, mode="r")
		downloaded_list = list(map(lambda i: i.rstrip(), f.readlines()))
		f.close()

		# 個別記事ページからの画像DL
		# 但し記事を無料範囲でダウンロード後、有料範囲で再度ダウンロードする際スキップされる（有料部分はダウンロードされない）ので
		# その場合downloaded.txtの該当urlを削除してから再実行してください
		print(f"★ {author}, {series_title} のダウンロードを開始します")
		for series_num, article_url in enumerate(download_target_urls):
			if article_url in downloaded_list:
				continue
			download_images(article_url, series_num+1, cookie)

			# ダウンロード後、記事urlをdownloaded.txtに書き込み
			with open(downloaded_txt, mode="a") as f:
				f.writelines(f"{article_url}\n")
		print(f"★ {author}, {series_title} のダウンロードが完了しました")

if __name__ == "__main__":
	main()