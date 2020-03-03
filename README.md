![](https://github.com/jindaxiang/aktools/blob/master/example/images/AkTools_demo.png)

[![](https://github.com/jindaxiang/aktools/workflows/build/badge.svg)](https://github.com/jindaxiang/aktools/actions)

# AkTools

AkTools is a package for local HTTP server for AkShare!

It depends on AkShare and FastAPI.

```cmd
pip install aktools
```

## AkShare

[...]

## FastAPI

[...]

# Demo

## Installation[windows]

```cmd
pip install akshare
pip install fastapi[all]
```

## Run CMD command[windows]

    1. cd into the path of aktools: e.g., aktools/news/
    2. then type the cmd command ```uvicorn news_api:app --reload```, just as ```C:\Anaconda3\envs\ak_test\Lib\site-packages\aktools\news>uvicorn news_api:app --reload```
    3. type ```http://127.0.0.1:8000/amac_fund_abs``` in your chrome for test

# Test-R

R-Program

```r
library(RCurl)
library(jsonlite)

url <- "http://127.0.0.1:8000/stock_js_weibo_report_df"
temp_df <- getURI(url, .encoding = "utf-8")
inner_df <- fromJSON(temp_df)
df <- t(rbind(inner_df$name, inner_df$rate))
colnames(df) <- c("name", "rate")
print(df)
```

Result

```
   name       rate    
0  "北玻股份" "-10.06"
1  "乾照光电" "-10.00"
2  "紫江企业" "-10.02"
3  "铜峰电子" "10.08" 
4  "晶方科技" "-10.00"
5  "希努尔"   "4.90"  
6  "株冶集团" "0.00"  
7  "东方财富" "1.33"  
8  "秀强股份" "-9.96" 
9  "方直科技" "10.00" 
10 "三五互联" "10.04" 
11 "得润电子" "7.91"  
12 "泰达股份" "-2.19" 
13 "万达信息" "6.82"  
14 "台基股份" "-9.98" 
15 "牧原股份" "2.24"  
16 "长高集团" "9.93"  
17 "合肥城建" "10.04" 
18 "碧水源"   "9.17"  
19 "海陆重工" "-9.98" 
20 "中国软件" "-0.11" 
21 "苏大维格" "6.94"  
22 "立思辰"   "7.80"  
23 "涪陵榨菜" "4.39"  
24 "雪浪环境" "10.03" 
25 "湘电股份" "-5.74" 
26 "同花顺"   "2.15"  
27 "贵州茅台" "1.28"  
28 "万邦达"   "7.01"  
29 "东华科技" "9.99"  
30 "福建水泥" "6.62"  
31 "科斯伍德" "10.00" 
32 "国电南自" "10.08" 
33 "江淮汽车" "2.21"  
34 "欧菲光"   "-4.25" 
35 "太极实业" "-9.76" 
36 "华天科技" "-5.40" 
37 "宏润建设" "10.13" 
38 "新开普"   "9.71"  
39 "上峰水泥" "5.01"  
40 "中信证券" "0.24"  
41 "荣科科技" "10.07" 
42 "哈投股份" "0.91"  
43 "中国平安" "-0.05" 
44 "山东路桥" "10.00" 
45 "宜通世纪" "-9.13" 
46 "东易日盛" "9.95"  
47 "汉钟精机" "9.96"  
48 "三一重工" "4.73"  
49 "华塑控股" "10.19"
```
