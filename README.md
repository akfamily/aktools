**《AKShare-初阶-使用教学》视频课程已经上线，本课程手把手讲解 AKShare 和 AKTools 的环境配置和安装使用，还包含了众多衍生知识，[详情点击链接](https://zmj.xet.tech/s/wck86)!
Tips：加入 AKShare VIP 答疑群可以免费获取该视频课程。**

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/akshare.svg)](https://pypi.org/project/akshare/)
[![PyPI](https://img.shields.io/pypi/v/aktools.svg)](https://pypi.org/project/aktools/)
[![Downloads](https://pepy.tech/badge/aktools)](https://pepy.tech/project/aktools)
[![Documentation Status](https://readthedocs.org/projects/aktools/badge/)](https://aktools.akfamily.xyz/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![aktools](https://img.shields.io/badge/Data%20Science-AKShare-green)](https://github.com/akfamily/aktools)
[![Actions Status](https://github.com/akfamily/aktools/workflows/build/badge.svg)](https://github.com/akfamily/aktools/actions)
[![MIT Licence](https://img.shields.io/badge/license-MIT-blue)](https://github.com/akfamily/aktools/blob/master/LICENSE)
[![](https://img.shields.io/github/forks/akfamily/aktools)](https://github.com/akfamily/aktools)
[![](https://img.shields.io/github/stars/akfamily/aktools)](https://github.com/akfamily/aktools)
[![](https://img.shields.io/github/issues/akfamily/aktools)](https://github.com/akfamily/aktools)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)

# AKTools

AKTools is a package of HTTP API for AKShare! It depends on AKShare, FastAPI and Typer.

[AKTools](https://github.com/akfamily/aktools) 是一款用于快速搭建 [AKShare](https://github.com/akfamily/akshare) HTTP API 的工具，通过 [AKTools](https://github.com/akfamily/aktools)
可以利用一行命令来启动 HTTP 服务，从而让原本专属服务于 Python 用户的开源财经数据接口库 [AKShare](https://github.com/akfamily/akshare) 的使用
突破编程语言的限制。无论您使用的是 C/C++、Java、Go、Rust、Ruby、PHP、JavaScript、R、Matlab、Stata 等编程语言或软件都可以快速、轻松获取财经数据，助力您更好地展开研究和开发工作。

**[AKTools 中文文档](https://aktools.readthedocs.io/)**

## Installation

```shell
pip install aktools
```

## Upgrade

```shell
pip install aktools --upgrade -i https://pypi.org/simple  # AKTools's version should great than 0.0.70
```

## AKShare

[Please visit AKShare's Documentation](https://akshare.akfamily.xyz/)

## FastAPI

[Please visit FastAPI's Documentation](https://fastapi.tiangolo.com/)

## Typer

[Please visit Typer's Documentation](https://typer.tiangolo.com/)

## Fast Run

1. just type the cmd/bash command: `python -m aktools`
2. then type `http://127.0.0.1:8080/` in your Chrome and you can fetch your homepage and more information
3. if you just want to test data api, you can type `http://127.0.0.1:8080/api/public/stock_zh_a_hist` in your Chrome
4. if you want to set parameter for API, then you just type like `http://127.0.0.1:8080/api/public/stock_zh_a_hist?symbol=600000`

## Homepage

AKTools set a simple homepage for user to provide simple reference information. When you set up your
environment and deploy your local application, then you can type `http:127.0.0.1:8080` in your browser.
We are developing more functions now, please pay more attention!

## Demo

### Test-Postman

![](https://dss-1252952517.cos.ap-chengdu.myqcloud.com/image-20211209235248006.png)

### Test-R

R-Program

```
library(RCurl)  # 需要先安装该包
library(jsonlite)  # 需要先安装该包
options (warn = -1)  # 该行有助于在无参数请求时去掉 warning 信息

temp_df <-
  getForm(
    uri = 'http://127.0.0.1:8080/api/public/stock_zh_a_hist',  # 此处的 http://127.0.0.1:8080 需要替换为您定义的地址和端口
    symbol = '000001',
    period = 'daily',
    start_date = '20211109',
    end_date = '20211209',
    adjust = 'hfq',
    .encoding = "utf-8"
  )
inner_df <- fromJSON(temp_df)
inner_df
```

R-Result

```shell
         日期    开盘    收盘    最高    最低      成交量     成交额    振幅  涨跌幅  涨跌额 换手率
1  2021-11-09 3009.83 3017.96 3037.46 2974.07 1240573 2163193120 2.11   0.60  17.88   0.64
2  2021-11-10 3006.58 2996.83 3008.20 2957.82 1220851 2109735152 1.67  -0.70 -21.13   0.63
3  2021-11-11 2988.70 3151.23 3164.23 2983.82 2084729 3752413856 6.02   5.15 154.40   1.07
4  2021-11-12 3144.73 3138.23 3196.74 3112.22  957546 1753072720 2.68  -0.41 -13.00   0.49
5  2021-11-15 3151.23 3164.23 3196.74 3126.85  655090 1203764096 2.23   0.83  26.00   0.34
6  2021-11-16 3152.85 3130.10 3182.11 3121.97  601110 1099113408 1.90  -1.08 -34.13   0.31
7  2021-11-17 3118.72 3112.22 3143.10 3091.09  664640 1203859184 1.66  -0.57 -17.88   0.34
8  2021-11-18 3108.97 3061.84 3113.85 3050.46  799844 1430058304 2.04  -1.62 -50.38   0.41
9  2021-11-19 3061.84 3118.72 3133.35 3045.58  786372 1414506384 2.87   1.86  56.88   0.41
10 2021-11-22 3099.22 3113.85 3134.97 3078.09  738618 1337768176 1.82  -0.16  -4.87   0.38
11 2021-11-23 3112.22 3074.84 3151.23 3042.33 1235978 2213817584 3.50  -1.25 -39.01   0.64
12 2021-11-24 3056.96 3073.21 3086.22 3039.08  741311 1316774400 1.53  -0.05  -1.63   0.38
13 2021-11-25 3052.09 3042.33 3060.21 3034.21  603533 1068221312 0.85  -1.00 -30.88   0.31
14 2021-11-26 3032.58 3026.08 3040.71 3016.33  694500 1219937312 0.80  -0.53 -16.25   0.36
15 2021-11-29 2998.45 3014.70 3024.46 2990.33  512595  895105984 1.13  -0.38 -11.38   0.26
16 2021-11-30 3019.58 3003.33 3042.33 2988.70  733616 1280384560 1.78  -0.38 -11.37   0.38
17 2021-12-01 3001.70 3035.83 3056.96 2991.95  706925 1243666848 2.16   1.08  32.50   0.36
18 2021-12-02 3032.58 3027.71 3063.46 2991.95  994798 1749164560 2.36  -0.27  -8.12   0.51
19 2021-12-03 3035.83 3037.46 3045.58 2998.45  707600 1242375056 1.56   0.32   9.75   0.36
20 2021-12-06 3069.96 3110.60 3185.36 3061.84 2145625 3896385168 4.07   2.41  73.14   1.11
21 2021-12-07 3143.10 3169.11 3203.24 3118.72 1616444 2979968976 2.72   1.88  58.51   0.83
22 2021-12-08 3167.48 3170.73 3183.73 3120.35  980281 1798691056 2.00   0.05   1.62   0.51
23 2021-12-09 3173.98 3208.11 3266.62 3154.48 1455887 2726663440 3.54   1.18  37.38   0.75
```

### Test-MATLAB

MATLAB-Program

```
api = 'http://127.0.0.1:8080/api/public/';
url = [api 'stock_zh_a_hist'];
options = weboptions('ContentType','json', 'CharacterEncoding', 'utf-8');
data = webread(url, options, symbol = '000001', period = 'daily', start_date = '20211109', end_date = '20211209', adjust = 'hfq');
data % 由于 MATLAB 无法显示中文字段名，请自行修改为英文字段，参考链接：https://iso2mesh.sourceforge.net/cgi-bin/index.cgi?jsonlab/Doc/Examples
```

MATLAB-Result

```shell
'2021-11-09'	3009.83000000000	3017.96000000000	3037.46000000000	2974.07000000000	1240573	2163193120.00000	2.11000000000000	0.600000000000000	17.8800000000000	0.640000000000000
'2021-11-10'	3006.58000000000	2996.83000000000	3008.20000000000	2957.82000000000	1220851	2109735152.00000	1.67000000000000	-0.700000000000000	-21.1300000000000	0.630000000000000
'2021-11-11'	2988.70000000000	3151.23000000000	3164.23000000000	2983.82000000000	2084729	3752413856.00000	6.02000000000000	5.15000000000000	154.400000000000	1.07000000000000
'2021-11-12'	3144.73000000000	3138.23000000000	3196.74000000000	3112.22000000000	957546	1753072720.00000	2.68000000000000	-0.410000000000000	-13	0.490000000000000
'2021-11-15'	3151.23000000000	3164.23000000000	3196.74000000000	3126.85000000000	655090	1203764096.00000	2.23000000000000	0.830000000000000	26	0.340000000000000
'2021-11-16'	3152.85000000000	3130.10000000000	3182.11000000000	3121.97000000000	601110	1099113408.00000	1.90000000000000	-1.08000000000000	-34.1300000000000	0.310000000000000
'2021-11-17'	3118.72000000000	3112.22000000000	3143.10000000000	3091.09000000000	664640	1203859184.00000	1.66000000000000	-0.570000000000000	-17.8800000000000	0.340000000000000
'2021-11-18'	3108.97000000000	3061.84000000000	3113.85000000000	3050.46000000000	799844	1430058304.00000	2.04000000000000	-1.62000000000000	-50.3800000000000	0.410000000000000
'2021-11-19'	3061.84000000000	3118.72000000000	3133.35000000000	3045.58000000000	786372	1414506384.00000	2.87000000000000	1.86000000000000	56.8800000000000	0.410000000000000
'2021-11-22'	3099.22000000000	3113.85000000000	3134.97000000000	3078.09000000000	738618	1337768176.00000	1.82000000000000	-0.160000000000000	-4.87000000000000	0.380000000000000
'2021-11-23'	3112.22000000000	3074.84000000000	3151.23000000000	3042.33000000000	1235978	2213817584.00000	3.50000000000000	-1.25000000000000	-39.0100000000000	0.640000000000000
'2021-11-24'	3056.96000000000	3073.21000000000	3086.22000000000	3039.08000000000	741311	1316774400.00000	1.53000000000000	-0.0500000000000000	-1.63000000000000	0.380000000000000
'2021-11-25'	3052.09000000000	3042.33000000000	3060.21000000000	3034.21000000000	603533	1068221312.00000	0.850000000000000	-1	-30.8800000000000	0.310000000000000
'2021-11-26'	3032.58000000000	3026.08000000000	3040.71000000000	3016.33000000000	694500	1219937312.00000	0.800000000000000	-0.530000000000000	-16.2500000000000	0.360000000000000
'2021-11-29'	2998.45000000000	3014.70000000000	3024.46000000000	2990.33000000000	512595	895105984	1.13000000000000	-0.380000000000000	-11.3800000000000	0.260000000000000
'2021-11-30'	3019.58000000000	3003.33000000000	3042.33000000000	2988.70000000000	733616	1280384560.00000	1.78000000000000	-0.380000000000000	-11.3700000000000	0.380000000000000
'2021-12-01'	3001.70000000000	3035.83000000000	3056.96000000000	2991.95000000000	706925	1243666848.00000	2.16000000000000	1.08000000000000	32.5000000000000	0.360000000000000
'2021-12-02'	3032.58000000000	3027.71000000000	3063.46000000000	2991.95000000000	994798	1749164560.00000	2.36000000000000	-0.270000000000000	-8.12000000000000	0.510000000000000
'2021-12-03'	3035.83000000000	3037.46000000000	3045.58000000000	2998.45000000000	707600	1242375056.00000	1.56000000000000	0.320000000000000	9.75000000000000	0.360000000000000
'2021-12-06'	3069.96000000000	3110.60000000000	3185.36000000000	3061.84000000000	2145625	3896385168.00000	4.07000000000000	2.41000000000000	73.1400000000000	1.11000000000000
'2021-12-07'	3143.10000000000	3169.11000000000	3203.24000000000	3118.72000000000	1616444	2979968976.00000	2.72000000000000	1.88000000000000	58.5100000000000	0.830000000000000
'2021-12-08'	3167.48000000000	3170.73000000000	3183.73000000000	3120.35000000000	980281	1798691056.00000	2	0.0500000000000000	1.62000000000000	0.510000000000000
'2021-12-09'	3173.98000000000	3208.11000000000	3266.62000000000	3154.48000000000	1455887	2726663440.00000	3.54000000000000	1.18000000000000	37.3800000000000	0.750000000000000
```

### Test-Rust

Rust-Program

```rust
use reqwest::blocking;
use serde_json::Value;
use std::collections::HashMap;

// 定义常量，用于存储API的URL。
const URL: &str = "http://127.0.0.1:8080/api/public";

/// 获取股票数据的函数。
///
/// # 参数
/// * `symbol` - 股票代码。
/// * `period` - 时间周期。
/// * `start_date` - 开始日期。
/// * `end_date` - 结束日期。
/// * `adjust` - 复权类型。
///
/// # 返回值
/// 返回一个Result，如果成功返回空的Ok，如果失败返回错误。
fn get_data(
    endpoint: &str,
    symbol: &str,
    period: &str,
    start_date: &str,
    end_date: &str,
    adjust: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    // 初始化查询参数，使用提供的函数参数。
    let params = HashMap::from([
        ("symbol", symbol),
        ("period", period),
        ("start_date", start_date),
        ("end_date", end_date),
        ("adjust", adjust),
    ]);

    // 创建一个阻塞的HTTP客户端。
    let client = blocking::Client::new();
    // 构建HTTP GET请求，并将查询参数附加到请求上。
    let full_url = format!("{}/{}", URL, endpoint);
    let resp = client.get(full_url).query(&params).send()?;

    // 检查响应状态码是否表示成功。
    if resp.status().is_success() {
        // 解析响应体为JSON并打印。
        let stock_data_list: Value = resp.json()?;
        println!("{:#?}", stock_data_list);
    } else {
        // 如果响应不是成功的，则打印错误信息。
        eprintln!("请求失败，状态码为: {}", resp.status());
    }

    Ok(())
}

fn main() {
    // 调用`get_data`函数，并传递股票参数。
    // 如果出现错误，则打印错误信息。
    if let Err(e) = get_data("stock_zh_a_hist", "000001", "daily", "20240125", "20240127", "") {
        eprintln!("发生错误: {}", e);
    }
}
```

Rust-Result

```shell
Array [
    Object {
        "开盘": Number(9.33),
        "成交量": Number(2162514),
        "成交额": Number(2037648413.07),
        "振幅": Number(2.89),
        "换手率": Number(1.11),
        "收盘": Number(9.5),
        "日期": String("2024-01-25T00:00:00.000"),
        "最低": Number(9.27),
        "最高": Number(9.54),
        "涨跌幅": Number(1.82),
        "涨跌额": Number(0.17),
    },
    Object {
        "开盘": Number(9.47),
        "成交量": Number(2272287),
        "成交额": Number(2172799799.01),
        "振幅": Number(2.42),
        "换手率": Number(1.17),
        "收盘": Number(9.62),
        "日期": String("2024-01-26T00:00:00.000"),
        "最低": Number(9.44),
        "最高": Number(9.67),
        "涨跌幅": Number(1.26),
        "涨跌额": Number(0.12),
    },
]
```
