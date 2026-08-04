from goal2_sourcing_engine._archive.replica_yupoo.reddit_designer_scout import RedditDesignerScout

scout = RedditDesignerScout()
text = "Check out these links! https://item.taobao.com/item.htm?id=12345, https://weidian.com/item.html?itemID=67890. Also https://1688.com/offer/111.html"
links = scout.extract_links(text)

assert "https://item.taobao.com/item.htm?id=12345" in links
assert "https://weidian.com/item.html?itemID=67890" in links
assert "https://1688.com/offer/111.html" in links

print("Links extracted correctly!", links)
