# d-book
online book store based-on block-chain
# 环境准备
## 0x1, 安装docker
```shell
参考https://docs.docker.com/engine/install/
```

## 0x2, 安装docker-compose(windows跳过此步骤)
```shell
参考https://docs.docker.com/compose/install/
```
## 0x3, 启动server
```shell
//进入项目根目录
docker-compose up --build
```
## 0x4, 关闭server
```shell
//进入项目根目录
docker-compose down
```
## 0x5, 访问api doc
```shell
http://localhost:8000/api-doc //登录用户: admin/admin
```
## 0x6, api登录认证
```shell
headers: {
  "authorization": "Bearer {token}"
}
```
# API
## Mobile Client
```html
1, login
http://localhost/api/v1/login
method: post
2, 获取登录随机数
http://localhost/api/v1/nonce
method: post
3, logout
http://localhost/api/v1/logout
method: post
3, 个人资产
http://localhost/api/v1/assets
methods: get
4, 书签
http://localhost/api/v1/bookmarks
methods: patch
5, 阅读书籍
http://localhost/api/v1/assets/{id}/read
methods: get
```
## Web Client
```html
1, login
http://localhost/api/v1/login
method: post
2, 获取登录随机数
http://localhost/api/v1/nonce
method: post
3, logout
http://localhost/api/v1/logout
method: post
3, 个人资产
http://localhost/api/v1/assets
methods: get
4, 书签
http://localhost/api/v1/bookmarks
methods: patch
5, 书籍
http://localhost/api/v1/issues
methods: post, patch, get
6, banner
http://localhost/api/v1/banners
methods: post, patch, get, delete
7, 挂单
http://localhost/api/v1/trades
methods: post, patch, get, delete
8, 购买
http://localhost/api/v1/transactions
methods: post, get
9, 合约
http://localhost/api/v1/contracts
methods: post, patch, get, delete
10, 书籍分类
http://localhost/api/v1/categories
methods: post, patch, get, delete
```