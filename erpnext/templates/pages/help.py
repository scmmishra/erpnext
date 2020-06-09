from __future__ import unicode_literals
import frappe, json
from frappe.utils.user import is_website_user
from frappe import _
import requests

def get_context(context):
	context.no_cache = 1
	context.align_greeting = ''
	settings = frappe.get_doc("Support Settings")

	context.greeting_text = settings.greeting_text
	context.subtitle = settings.subtitle

	# Support content
	favorite_article_count = 0
	context.favorite_article_list=[]
	context.help_article_list=[]
	context.docs_search_scope = "kb"
	context.category_list = frappe.get_all("Help Category", fields="name")
	favorite_articles = get_favorite_articles()

	for article in favorite_articles:
		favorite_article_dict = {}
		description = frappe.utils.strip_html(article.content)
		if len(description) > 150:
			description = description[:150] + '...'
		favorite_article_dict = {
					'title': article.title,
					'description': description,
					'route': article.route,
					'category': article.category,
				}
		context.favorite_article_list.append(favorite_article_dict)

	for category in context.category_list:
		help_aricles_per_category = {}
		help_articles = frappe.get_all("Help Article", fields="*", filters={"category": category.name}, order_by="modified desc", limit=5)
		if len(help_articles):
			help_aricles_per_caetgory = {
				'category': category,
				'articles': help_articles,
			}
			context.help_article_list.append(help_aricles_per_caetgory)

	# Issues
	ignore_permissions = False
	if is_website_user():
		ignore_permissions = True
	if frappe.session.user != "Guest":
		context.issues = frappe.get_list("Issue", fields=["name", "status", "subject", "modified"], ignore_permissions=ignore_permissions)[:3]
	else:
		context.issues = []

def get_favorite_articles():
	ranked_articles = frappe.db.sql("""
			SELECT
				t1.title as title,
				t1.content as content,
				t1.route as route,
				t1.category as category,
				count(t1.route) as count
			FROM
				`tabHelp Article` AS t1
				INNER JOIN
				`tabWeb Page View` AS t2
			ON t1.route = t2.path
			GROUP BY route
			ORDER BY count DESC
			LIMIT 6;
	""", as_dict=1)
	if len(ranked_articles):
		return ranked_articles
	else:
		return frappe.get_list("Help Article", fields=['title', 'content', 'route', 'category'], filters={"published": 1}, limit=6)
