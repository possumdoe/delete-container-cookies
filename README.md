# delete-container-cookies

Firefox container's cookie deleter

## Before

1. In order to execute this script correctly, it is essential to close **all active Firefox windows**.

2. The Firefox profile being targeted is the **most recently accessed one**.

## Usage

Delete all cookies, from **all containers** (even the "no container" one's)

```bash
./delete_container_cookies.py --browser firefox
```

Delete all cookies from **container CONTAINER**   

```bash
./delete_container_cookies.py --browser firefox --container CONTAINER
```

Delete all "no container" cookies 

```bash
./delete_container_cookies.py --browser firefox --container none
```

## Credits

The structure and part of my code is taken from **yt-dlp**

https://github.com/yt-dlp/yt-dlp
