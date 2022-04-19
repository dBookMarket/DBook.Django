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
cd backend //进入项目根目录
docker-compose up --build
```
## 0x4, 关闭server
```shell
cd backend //进入项目根目录
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