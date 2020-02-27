# Do Github editor here

## FastAPI

## AkShare

R 语言调用代码

```
library(RCurl)
library(jsonlite)
url <- "http://127.0.0.1:8000/stock_em_account"
temp_df = getForm(url,.encoding="utf-8")
df = fromJSON(temp_df, simplifyDataFrame=TRUE)
print(df)
```