from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass, asdict
import feedparser
import inspect
import os
import re
import requests
from time import mktime
from typing import List


IMAGE_OVERRIDES = {
    'https://medium.com/@dstarner/exploring-snug-harbor-60f49bc40786': 'https://miro.medium.com/max/4000/1*m60t2-xheDbpcutjclU4lg.jpeg'
}


INDEX_PATH = './index.html'
API_KEY = os.getenv('DEV_TO_TOKEN')

DEFAULT_IMAGE = 'img/default-blog-image.webp'

TAG_TEMPLATE = """                                        <a href="#" title="View all posts in {tag}">{tag}</a>"""

TEMPLATE = """
                        <div class="item post-1">
                            <div class="blog-card">
                                <div class="media-block">
                                    <div class="category">
{tag_html}
                                    </div>
                                    <a href="{url}">
                                        <img src="{cover_image}" class="size-blog-masonry-image-two-c" alt="{title}" title="{title}" />
                                        <div class="mask"></div>
                                    </a>
                                </div>
                                <div class="post-info">
                                    <div class="post-details">
                                      <div class="post-date">{published_at}</div>
                                      <div class="post-views">{views_display}</div>
                                    </div>
                                    <a href="{url}">
                                        <h4 class="blog-item-title">{title}</h4>
                                    </a>
                                </div>
                            </div>
                        </div>
"""


@dataclass
class Article:

    title: str
    id: str
    description: str
    published: bool
    page_views_count: int
    tag_list: List[str]
    url: str
    published_timestamp: str
    cover_image: str
    published_dt: datetime = None

    def __str__(self) -> str:
        return self.title

    @classmethod
    def from_dict(cls, env):      
        obj = cls(**{
            k: v for k, v in env.items() 
            if k in inspect.signature(cls).parameters
        })
        if not obj.cover_image:
            obj.cover_image = DEFAULT_IMAGE
        if not obj.published_dt:
            obj.published_dt = datetime.strptime(obj.published_timestamp.split('T')[0], '%Y-%m-%d')
        return obj


def get_articles():
    dev_resp = requests.get('https://dev.to/api/articles/me', headers={'api-key': API_KEY}).json()
    dev_articles = [Article.from_dict(data) for data in dev_resp if data['published']]

    med_resp = feedparser.parse('https://medium.com/feed/@dstarner')
    med_articles = [Article(
        title=p['title'],
        id=p['id'],
        url=p['link'].split('?')[0],
        page_views_count='',
        description='',
        published=p['published'],
        tag_list=[t['term'] for t in p['tags']],
        cover_image=DEFAULT_IMAGE,
        published_timestamp='',
        published_dt=datetime.fromtimestamp(mktime(p['published_parsed']))
    ) for p in med_resp.entries]

    for article in med_articles:
        if article.url in IMAGE_OVERRIDES:
            article.cover_image = IMAGE_OVERRIDES[article.url]
            continue
        resp = requests.get(article.url)
        if resp.status_code != 200:
            print(f'could not load {article.url}')
            continue
        soup = BeautifulSoup(resp.text, 'html.parser').find('article')
        img = soup.find('img', {'role': 'presentation'})
        if img:
            article.cover_image = img['src']

    return sorted(
        dev_articles + med_articles,
        key=lambda a: a.published_dt, reverse=True,
    )

def article_to_html(article: Article):
    extras = {
        'published_at': article.published_dt.strftime('%d %B %Y'),
        'tag_html': '\n'.join([TAG_TEMPLATE.format(tag=tag) for tag in article.tag_list]),
        'views_display': f"{('<200' if article.page_views_count < 200 else article.page_views_count)} Views" if isinstance(article.page_views_count, int) else '', 
    }
    return TEMPLATE.format(**extras, **asdict(article))

def add_articles(articles):
    with open(INDEX_PATH, 'r') as f:
        content = f.read()

    post_content = ''.join([article_to_html(a) for a in articles])
    
    new_content, replacements = re.subn(
        r'<!-- DONOTREMOVE: BLOG-POSTS -->(\n|.)*<!-- /DONOTREMOVE: BLOG-POSTS -->',
        f'<!-- DONOTREMOVE: BLOG-POSTS -->{post_content}                        <!-- /DONOTREMOVE: BLOG-POSTS -->',
        content
    )

    s = 0
    for a in articles:
        try:
            s += int(a.page_views_count)
        except:
            pass
    
    views = round(s, -3)

    new_content, replacements = re.subn(r'id="view-count">(\n|.)*\+</span>', f'id="view-count">{views:,}+</span>', new_content)

    with open(INDEX_PATH, 'w') as f:
        f.write(new_content)


articles = get_articles()
add_articles(articles)
