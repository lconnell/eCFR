# AWS
region = "us-east-1"
project = "ecfr-agency-size"
suffix  = "dev"

# eCFR overrides
ecfr_base_url = "https://www.ecfr.gov"
ecfr_title_json_path_tmpl = "/api/versioner/v1/full/{date}/title-{title}.json"
http_user_agent = "ecfr-agency-size-lambda/1.0"

# Max titles to process (default 50)
ecfr_max_titles = 50
