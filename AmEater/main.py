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

class AmEater:
	"""ライター固有のID（writer_id）を受け取り、記事内の画像をDLします"""
	
	def __init__(self, writer_id):
		self.writer_id = writer_id
		self.writer_name = self.get_writername()
		self.mkdir_chdir()
		self.downloaded_list = self.get_downloaded_list()
		self.article_urls = self.get_article_urls()

	def get_writername(self):
		"""
		ライター名を取得する
		"""
		url = f"https://am-our.com/author/{self.writer_id}/"
		response = requests.get(url)
		soup = BeautifulSoup(response.text,'lxml')
		writername = soup.select(".breadcrumb__item.breadcrumb__item-current")[0].getText()
		return writername

	def mkdir_chdir(self):
		"""
		カレントディレクトリ（ダウンロードルートフォルダ）にダウンロード先フォルダの作成と移動
		"""
		dest_dir = os.path.join(os.getcwd(), self.writer_name)
		os.makedirs(dest_dir, exist_ok=True)
		os.chdir(dest_dir)

	def get_downloaded_list(self):
		"""
		カレントディレクトリのdownloaded.txtの作成と読み込み
		（ダウンロード先フォルダにCDしていることが前提）
		"""
		downloaded_txt = os.path.join(os.getcwd(), "downloaded.txt")

		# downloaded.txtの作成
		if not os.path.isfile(downloaded_txt):
			with open(downloaded_txt, mode="w") as f:
				f.write("")

		# downloaded.txtの読み込み
		with open(downloaded_txt, mode="r") as f:
			downloaded_list = list(map(lambda i: i.rstrip(), f.readlines()))

		return downloaded_list

	def get_article_urls(self):
		"""
		writer_idからダウンロード対象となる記事個別URLを取得し、ソート済みリストで返す
		"""
		article_infos = []
		page_num = 0
		while True:
			page_num += 1
			request_url = f"https://am-our.com/author/{self.writer_id}/page/{page_num}/"
			response = requests.get(request_url)
			if response.status_code == 404: # ページ遷移先がなくなった時
				break

			soup = BeautifulSoup(response.text,'lxml')
			pages = soup.select(".archive_author_top.view-mask, .article_top_center.archive__item.view-mask")

			while pages:
				try:
					article = pages.pop()
					article_url = article.select(".eyecatch__link.eyecatch__link-mask-latest")[0].attrs["href"]
					article_date = article.select(".dateList__item")[0].contents[0].strip()
					article_infos.append({"article_url": article_url, "article_date": article_date})
				except Exception as e:
					print(e)

		# 投稿日付昇順でソート
		article_infos.sort(key=lambda x: x["article_date"])
		return article_infos

	def download_images(self, page_url, series_num):
		"""
		個別ページのurlから画像をダウンロードする
		但し記事によってはhtmlが異なることに注意

		Parameters
		---
		page_url: str
			ダウンロードしたい画像へのリンクを含む、個別記事のurl
		series_num: int
			連載の中の第何話目かを示す変数
		"""

		response = requests.get(page_url)
		soup = BeautifulSoup(response.text,'lxml')

		if page_url in self.downloaded_list: # ダウンロード済みの場合
			return

		else: # 未ダウンロードの場合
			article_title = soup.select(".heading.heading-primary")[0].getText()
			article_title = f"{str(series_num)}_{article_title}"
			print(f"★ {article_title} をダウンロードします")

			# パターン１
			# 例：https://am-our.com/love/110/17022/
			if soup.select(".photo img"):
				img_cnt = 1
				self.download_images_class_photo(soup, article_title, img_cnt)
				self.append_downloaded_txt(page_url)

			# パターン２
			# 例：https://am-our.com/love/103245/
			elif soup.select(".aligncenter"):
				self.download_images_class_aligncenter(soup, article_title)
				self.append_downloaded_txt(page_url)
				
			else: # ダウンロード用のコードが用意されていないパターンの場合
				print("★ 未定義urlです")
				print(f"★ {series_num} {article_title} をダウンロードできませんでした")

		return

	def append_downloaded_txt(self, string):
		with open("downloaded.txt", mode="a") as f:
			f.writelines(f"{string}\n")

	def download_images_class_photo(self, soup, article_title, img_cnt):
		for img_idx in range(len(soup.select(".photo img"))):
			img_url = soup.select(".photo img")[img_idx].get("src")
			filename = f"{article_title}_{img_cnt}.png" # png以外の拡張子が存在する場合は書き方変える必要あり
			image = requests.get(img_url).content
			try:
				with open(filename, mode="wb") as file:
					file.write(image)
			except Exception as e:
				print(e)
				return
			img_cnt += 1

		# 次のページがあるなら遷移して処理する
		if soup.select(".next_page"):
			nextpage_url = soup.select(".next_page_block")[0].get("href")
			response = requests.get(nextpage_url)
			soup = BeautifulSoup(response.text,'lxml')
			self.download_images_class_photo(soup, article_title, img_cnt)
	
	def download_images_class_aligncenter(self, soup, article_title):
		page_idx = 0
		while True:
			page_idx += 1
			url_with_idx = f"{page_url}{page_idx}/"
			response = requests.get(url_with_idx)
			if response.status_code == 404:
				break
			soup = BeautifulSoup(response.text,'lxml')
			img_url = soup.select(".aligncenter.is-resized")[0].select("img")[0].get("src")
			filename = f"{article_title}_{page_idx}.png" # png以外の拡張子が存在する場合は書き方変える必要あり
			image = requests.get(img_url).content
			try:
				with open(filename, mode="wb") as file:
					file.write(image)
			except Exception as e:
				print(e)
				return

				
def main():
	print("★ starting am-eater...")
	root_dir = os.path.dirname(os.path.abspath(__file__))
	os.chdir(root_dir)

	writers = read_settings()
	for writer_id in writers:
		Writer = AmEater(writer_id)
		for series_num, url_dict in enumerate(Writer.article_urls, start=1):
			url = url_dict["article_url"]
			Writer.download_images(url, series_num)

		print("オワリ")

if __name__ == "__main__":
	main()

