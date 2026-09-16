<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

$feeds = [
  'magic-mile-media' => 'https://www.magicmilemedia.com/blog?format=rss',
  'neuse-news' => 'https://www.neusenews.com/index?format=rss',
  'neuse-news-sports' => 'https://www.neusenewssports.com/news-1?format=rss',
  'neuse-news-sports-wayne' => 'https://www.nnswayne.com/news?format=rss',
  'nc-business-desk' => 'https://ncbusinessdesk.com/feed/',
  'nc-political-news' => 'https://www.ncpoliticalnews.com/news?format=rss',
];
$brand = (string)($_GET['brand'] ?? '');
if (!isset($feeds[$brand])) { http_response_code(400); echo json_encode(['error' => 'Unknown brand.']); exit; }

$request = curl_init($feeds[$brand]);
curl_setopt_array($request, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => true, CURLOPT_TIMEOUT => 20, CURLOPT_USERAGENT => 'Local Voice Engine RSS Reader/1.0']);
$xmlText = curl_exec($request);
$status = (int)curl_getinfo($request, CURLINFO_HTTP_CODE);
curl_close($request);
if ($xmlText === false || $status >= 400) { http_response_code(502); echo json_encode(['error' => 'Unable to retrieve this feed right now.']); exit; }

libxml_use_internal_errors(true);
$xml = simplexml_load_string($xmlText, 'SimpleXMLElement', LIBXML_NOCDATA);
if ($xml === false || !isset($xml->channel->item)) { http_response_code(502); echo json_encode(['error' => 'The source did not return a readable RSS feed.']); exit; }
$items = [];
foreach ($xml->channel->item as $item) {
  $title = trim((string)$item->title);
  $link = trim((string)$item->link);
  $description = trim(html_entity_decode(strip_tags((string)$item->description), ENT_QUOTES | ENT_HTML5, 'UTF-8'));
  $media = $item->children('http://www.rssboard.org/media-rss');
  $imageUrl = isset($media->content) ? trim((string)$media->content->attributes()->url) : '';
  $items[] = ['id' => sha1($link ?: $title), 'title' => $title, 'link' => $link, 'publishedAt' => (string)$item->pubDate, 'description' => mb_strimwidth($description, 0, 300, '…', 'UTF-8'), 'imageUrl' => $imageUrl];
  if (count($items) === 10) break;
}
echo json_encode(['brand' => $brand, 'refreshedAt' => gmdate(DATE_ATOM), 'items' => $items], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
