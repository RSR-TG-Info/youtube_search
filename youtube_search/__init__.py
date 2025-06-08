
import requests
import urllib.parse
import json

class YoutubeSearch:
    def __init__(self, search_terms: str, max_results=None):
        self.search_terms = search_terms
        self.max_results = max_results
        self.videos = self._search()
    
    def _search(self):
        encoded_search = urllib.parse.quote_plus(self.search_terms)
        BASE_URL = "https://youtube.com"
        url = f"{BASE_URL}/results?search_query={encoded_search}"
        response = requests.get(url).text
        while "ytInitialData" not in response:
            response = requests.get(url).text
        results = self._parse_html(response)
        if self.max_results is not None and len(results) > self.max_results:
            return results[: self.max_results]
        return results
    
    def _parse_html(self, response):
        results = []
        try:
            start = (
                response.index("ytInitialData")
                + len("ytInitialData")
                + 3
            )
            end = response.index("};", start) + 1
            json_str = response[start:end]
            data = json.loads(json_str)
            
            contents_path = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
            
            for contents in contents_path:
                item_section = contents.get("itemSectionRenderer", {}).get("contents", [])
                for video in item_section:
                    if "videoRenderer" in video:
                        res = self._extract_video_data(video["videoRenderer"])
                        if res: 
                            results.append(res)
                
                
        except (ValueError, KeyError, IndexError) as e:
            print(f"Error parsing HTML: {e}")
            
        return results
    
    def _extract_video_data(self, video_data):
        """Extract video data with better error handling"""
        try:
            res = {}
            
            res["id"] = video_data.get("videoId")
            
            thumbnails = video_data.get("thumbnail", {}).get("thumbnails", [])
            res["thumbnails"] = [thumb.get("url") for thumb in thumbnails if thumb.get("url")]
            
            title_runs = video_data.get("title", {}).get("runs", [])
            res["title"] = title_runs[0].get("text") if title_runs else None
            
            desc_runs = video_data.get("descriptionSnippet", {}).get("runs", [])
            res["long_desc"] = desc_runs[0].get("text") if desc_runs else None
            
            channel_name = None
            
            if "longBylineText" in video_data:
                runs = video_data["longBylineText"].get("runs", [])
                if runs:
                    channel_name = runs[0].get("text")
            
            if not channel_name and "shortBylineText" in video_data:
                runs = video_data["shortBylineText"].get("runs", [])
                if runs:
                    channel_name = runs[0].get("text")
            
            if not channel_name and "ownerText" in video_data:
                runs = video_data["ownerText"].get("runs", [])
                if runs:
                    channel_name = runs[0].get("text")
            
            res["channel"] = channel_name
            
            res["duration"] = video_data.get("lengthText", {}).get("simpleText", "N/A")
            
            view_count = video_data.get("viewCountText", {})
            if isinstance(view_count, dict):
                res["views"] = view_count.get("simpleText", "N/A")
            else:
                res["views"] = "N/A"
            
            publish_time = video_data.get("publishedTimeText", {})
            if isinstance(publish_time, dict):
                res["publish_time"] = publish_time.get("simpleText", "N/A")
            else:
                res["publish_time"] = "N/A"
            
            nav_endpoint = video_data.get("navigationEndpoint", {})
            web_command = nav_endpoint.get("commandMetadata", {}).get("webCommandMetadata", {})
            res["url_suffix"] = web_command.get("url")
            
            return res
            
        except Exception as e:
            print(f"Error extracting video data: {e}")
            return None
    
    def to_dict(self, clear_cache=True):
        result = self.videos
        if clear_cache:
            self.videos = []
        return result
    
    def to_json(self, clear_cache=True):
        result = json.dumps({"videos": self.videos}, indent=2)
        if clear_cache:
            self.videos = []
        return result
