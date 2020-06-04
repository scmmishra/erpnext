from __future__ import unicode_literals
import frappe, json

import requests

def get_context(context):
	context.no_cache = 1
	context.bg = 'background-color: #fafbfc; border-radius:0'
	context.align_greeting = 'start'
	context.align_search_box = '0'
	settings = frappe.get_doc("Support Settings", "Support Settings")
	s = settings

	context.greeting_text = s.greeting_text if s.greeting_text else "We're here to help"

	if s.greeting_text_and_search_bar_alignment == 'Center':
		context.align_greeting = 'center'
		context.align_search_box = '25%'
	if s.greeting_text_and_search_bar_alignment == 'Right':
		context.align_greeting = 'end'
		context.align_search_box = '50%'
	if s.background == 'Color' and s.select_color:
		context.bg = 'background-color: ' + s.select_color + '; border-radius:0'
	if s.background == 'Image' and s.add_image:
		context.bg = 'background-image: url(' + s.add_image + '); background-repeat: no-repeat; border-radius:0'

	# Support content
	favorite_article_count = 0
	portal_setting = frappe.get_single("Portal Settings")
	context.favorite_article_list=[]
	context.help_article_list=[]
	context.category_list = frappe.get_all("Help Category", fields="name")
	all_articles = [i[0] for i in frappe.db.sql("""SELECT route from `tabHelp Article`""")]
	favorite_articles = get_favorite_articles()
	for article in favorite_articles:
		favorite_article_dict = {}
		if favorite_article_count < 3:
			if article[0] in all_articles:
				favorite_article = frappe.get_all("Help Article", fields=["title", "content", "route", "category"], filters={"route": article[0]})
				content = frappe.utils.strip_html(favorite_article[0].content)
				if len(content) > 115:
					content = content[:112] + '...'	
				favorite_article_dict = {
					'title': favorite_article[0].title,
					'content': content,
					'category': favorite_article[0].category,
					'route': favorite_article[0].route,
				}
				context.favorite_article_list.append(favorite_article_dict)
				favorite_article_count += 1			

	for category in context.category_list:
		help_aricles_per_category = {}
		help_articles = frappe.get_all("Help Article", fields="*", filters={"category": category.name}, order_by="modified desc", limit=5)
		help_aricles_per_caetgory = {
			'category': category,
			'articles': help_articles,
		}
		context.help_article_list.append(help_aricles_per_caetgory)

	# Get Started sections
	if s.get_started_sections:
		sections = json.loads(s.get_started_sections)
		context.get_started_sections = sections

	# Forum posts
	if s.show_latest_forum_posts:
		topics_data, post_params = get_forum_posts(s)
		context.post_params = post_params
		context.forum_url = s.forum_url
		context.topics = topics_data[:3]

	# Issues
	if frappe.session.user != "Guest":
		context.issues = frappe.get_all("Issue", fields=["name", "status", "subject", "modified"])[:3]
	else:
		context.issues = []

def get_forum_posts(s):
	response = requests.get(s.forum_url + '/' + s.get_latest_query)
	response.raise_for_status()
	response_json = response.json()

	topics_data = {} # it will actually be an array
	key_list = s.response_key_list.split(',')
	for key in key_list:
		topics_data = response_json.get(key) if not topics_data else topics_data.get(key)

	for topic in topics_data:
		topic["link"] = s.forum_url + '/' + s.post_route_string + '/' + str(topic.get(s.post_route_key))

	post_params = {
		"title": s.post_title_key,
		"description": s.post_description_key
	}
	return topics_data, post_params

def get_favorite_articles():
	return frappe.db.sql(
			"""SELECT path, COUNT(*)
				FROM `tabWeb Page View`
				GROUP BY path
				ORDER BY COUNT(*) DESC""")