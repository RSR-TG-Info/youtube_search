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
        
        try:
            response = requests.get(url).text
            while "ytInitialData" not in response:
                response = requests.get(url).text
            results = self._parse_html(response)
            if self.max_results is not None and len(results) > self.max_results:
                return results[: self.max_results]
            return results
        except Exception as e:
            print(f"Error in search: {e}")
            return []
    
    def _parse_html(self, response):
        results = []
        try:
            start = response.index("ytInitialData") + len("ytInitialData") + 3
            end = response.index("};", start) + 1
            json_str = response[start:end]
            data = json.loads(json_str)
            
            try:
                contents = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]
            except KeyError as e:
                print(f"Could not find expected JSON structure: {e}")
                return []
            
            for section in contents:
                if "itemSectionRenderer" not in section:
                    continue
                    
                items = section["itemSectionRenderer"]["contents"]
                for item in items:
                    if "videoRenderer" in item:
                        video_data = item["videoRenderer"]
                        video_info = self._extract_video_info(video_data)
                        if video_info:
                            results.append(video_info)
            
        except (ValueError, KeyError, IndexError) as e:
            print(f"Error parsing HTML: {e}")
            
        return results
    
    def _extract_video_info(self, video_data):
        """Extract video information with comprehensive channel name detection"""
        try:
            res = {}
            
            res["id"] = video_data.get("videoId", "N/A")
            
            thumbnails = video_data.get("thumbnail", {}).get("thumbnails", [])
            res["thumbnails"] = [thumb.get("url", "") for thumb in thumbnails]
            
            title_data = video_data.get("title", {})
            if "runs" in title_data and title_data["runs"]:
                res["title"] = title_data["runs"][0].get("text", "N/A")
            elif "simpleText" in title_data:
                res["title"] = title_data["simpleText"]
            else:
                res["title"] = "N/A"
            
            desc_data = video_data.get("descriptionSnippet", {})
            if "runs" in desc_data and desc_data["runs"]:
                res["long_desc"] = desc_data["runs"][0].get("text", "N/A")
            else:
                res["long_desc"] = "N/A"
            
            channel_name = self._extract_channel_name(video_data)
            res["channel"] = channel_name
            
            length_data = video_data.get("lengthText", {})
            res["duration"] = length_data.get("simpleText", "N/A")
            
            view_data = video_data.get("viewCountText", {})
            res["views"] = view_data.get("simpleText", "N/A")
            
            publish_data = video_data.get("publishedTimeText", {})
            res["publish_time"] = publish_data.get("simpleText", "N/A")
           
            nav_data = video_data.get("navigationEndpoint", {})
            command_data = nav_data.get("commandMetadata", {})
            web_data = command_data.get("webCommandMetadata", {})
            res["url_suffix"] = web_data.get("url", "N/A")
            
            return res
            
        except Exception as e:
            print(f"Error extracting video info: {e}")
            print("Problematic video_data keys:", list(video_data.keys()))
            return None
    
    def _extract_channel_name(self, video_data):
        """Try multiple methods to extract channel name"""
        
        try:
            long_byline = video_data.get("longBylineText", {})
            if "runs" in long_byline and long_byline["runs"]:
                channel_name = long_byline["runs"][0].get("text")
                if channel_name:
                    return channel_name
        except:
            pass
         
        try:
            short_byline = video_data.get("shortBylineText", {})
            if "runs" in short_byline and short_byline["runs"]:
                channel_name = short_byline["runs"][0].get("text")
                if channel_name:
                    return channel_name
        except:
            pass
       
        try:
            owner_text = video_data.get("ownerText", {})
            if "runs" in owner_text and owner_text["runs"]:
                channel_name = owner_text["runs"][0].get("text")
                if channel_name:
                    return channel_name
        except:
            pass
        
        try:
            for field in ["longBylineText", "shortBylineText", "ownerText"]:
                byline_data = video_data.get(field, {})
                if "simpleText" in byline_data:
                    return byline_data["simpleText"]
        except:
            pass
        
        
        print(f"Could not find channel name. Available keys in video_data:")
        for key in video_data.keys():
            if "byline" in key.lower() or "owner" in key.lower() or "channel" in key.lower():
                print(f"  {key}: {video_data[key]}")
        
        return "Channel not found"
    
    def to_dict(self, clear_cache=True):
        result = self.videos.copy() if self.videos else []
        if clear_cache:
            self.videos = []
        return result
    
    def to_json(self, clear_cache=True):
        result = json.dumps({"videos": self.videos}, indent=2, ensure_ascii=False)
        if clear_cache:
            self.videos = []
        return result
