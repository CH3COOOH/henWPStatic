# WordPress Static Site Generator

This Python script converts a dynamic WordPress site into a static HTML version by crawling the site based on a provided sitemap. It not only retrieves HTML and embedded resources (such as images, scripts, and stylesheets) but also parses CSS files to download font files and other linked assets.

## Usage

```sh
python script.py <homepage_url> <sitemap_url> [dig]
```

### Parameters:
- `<homepage_url>`: The URL of the WordPress site's homepage.
- `<sitemap_url>`: The URL of the WordPress site's sitemap.
- `[dig]` (optional): If provided as `dig`, the script runs in **DIG mode**, enabling deeper crawling.

### Examples:

1. **Basic Usage**:
   ```sh
   python script.py https://example.com https://example.com/sitemap.xml
   ```

2. **DIG Mode** (for deeper crawling):
   ```sh
   python script.py https://example.com https://example.com/sitemap.xml dig
   ```

3. **Process a Single URL**:
   ```sh
   python script.py https://example.com https://example.com/sitemap.xml https://example.com/page
   ```

This command fetches and processes a single URL along with its related resources.

## Notes

1. Each time a static generation task is completed, the URLs of downloaded resources are saved in a `.known` file (e.g., `homepage.known`). When the tool runs again, it reads this file to avoid re-downloading unchanged resources, improving efficiency when updating the static site.
2. The tool attempts to automatically detect and download all resources, but some files may still require manual downloading.
3. **DIG mode** performs secondary parsing for every URL, making it significantly slower. If the goal is to retrieve `wp-content`, it is recommended to avoid DIG mode. Instead, directly download the `wp-content` directory from the WordPress server and upload it to the static site's root folder.

## Demo

Look at this: [blog.henchat.net](https://blog.henchat.net).