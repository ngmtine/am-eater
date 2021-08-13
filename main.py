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
	download_targets = []

	for page_num in range(1, 999):
		request_url = f"https://am-our.com/author/{writer_id}/page/{page_num}/"
		response = requests.get(request_url)
		soup = BeautifulSoup(response.text,'lxml')
		pages = soup.select(".archive_author_top.view-mask, .article_top_center.archive__item.view-mask")

		if pages == []: # ページ遷移先がなくなった時
			break

		while pages:
			try:
				article = pages.pop()
				# article_url = article.get("href")
				article_url = article.select(".eyecatch__link.eyecatch__link-mask-latest")[0].attrs["href"]
				article_date = article.select(".dateList__item")[0].contents[0].strip()
				download_targets.append({"article_url": article_url, "article_date": article_date})
			except Exception as e:
				print(e)

	return download_targets

def main():
	print("★ starting am-eater...")
	root_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(root_dir)

	writers = read_settings()

	# シリーズの全記事urlの取得と投稿日でソート
	for writer_id in writers:
		download_targets = get_download_target_urls(writer_id)
		download_targets.sort(key=lambda x: x["article_date"])

if __name__ == "__main__":
	main()

