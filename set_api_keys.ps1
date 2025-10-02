# Set API keys for AIvengers
$env:AI_API_KEY = "3d3d9894-4d54-51d7-a280-b2d6cafd218d"
$env:AI_API_BASE = "https://arvancloudai.ir/gateway/models/GPT-5/lMu4ODjvBBjQyC_uE46tfqmfz7-ce3JQbfy1PV287WR6owmK7yI0wZd0LtUab81KJlV02yhA_N2_I5HAVpJivhuaE-wvSL7mGuO6ppwhV8LKp4bm0U0HRbU6gHS1Uzzl6oFqlF96JX853D2NNczGfk4wZlDzwrRCsn4oCYowETYH9a_J3r46JdnDG7fg-vd0owPS_REzazCDWOUw0QNMsaiLmHSgoWtlBnqihC69qzU/v1"

Write-Host "API keys set for this session" -ForegroundColor Green
Write-Host "API Key: $($env:AI_API_KEY.Substring(0,10))..." -ForegroundColor Yellow
Write-Host "API Base: $($env:AI_API_BASE.Substring(0,50))..." -ForegroundColor Yellow

# Run the GUI application
python gui_app.py

