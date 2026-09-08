from seeed_dht import DHT
from time import sleep as sl
from urllib import request, parse

def thingspeak_http(t_tb, h_tb):
    channel_ID = "3467228"
    # Thay thế bằng Write API Key thực tế của kênh ThingSpeak của bạn
    write_api_key = "174NUQR8NK572V5Y"

    url = "https://api.thingspeak.com/update"

    # Chi con 2 field: field1 = nhiet do trung binh, field2 = do am trung binh
    post_data = parse.urlencode({
        'api_key': write_api_key,
        'field1': t_tb,
        'field2': h_tb
    }).encode('utf-8')

    try:
        req = request.Request(url, data=post_data, method="POST")

        # Thêm các header theo yêu cầu (đã tối ưu riêng cho Raspberry Pi 4)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        req.add_header('User-Agent', 'Python-RaspberryPi4/Client')

        with request.urlopen(req) as response:
            html = response.read().decode("utf-8")
            return html
    except Exception as e:
        print("Lỗi khi gửi HTTP POST lên ThingSpeak:", e)
        return None

def main():
    i = 0
    data1 = []
    data2 = []

    # Sử dụng DHT22 ở chân GPIO 5 trên Raspberry Pi 4
    sensor = DHT('22', 5)

    while True:
        i += 1
        humi, temp = sensor.read()

        # Kiểm tra dữ liệu tránh lỗi None khi đọc cảm biến thất bại
        if humi is None or temp is None:
            print("Đọc cảm biến DHT22 thất bại, đang thử lại...")
            i -= 1
            sl(2)
            continue

        data1.append(temp)
        data2.append(humi)

        sl(1)
        print('----------------------------------------------')

        tb1 = sum(data1) / len(data1)
        tb2 = sum(data2) / len(data2)

        tb1 = round(tb1, 1)
        tb2 = round(tb2, 1)

        print('Nhiet do:{0}C va Do am:{1}%'.format(temp, humi))
        print('Nhiet do TB:{0}C, Do am TB:{1}%'.format(tb1, tb2))

        # Gui nhiet do TB, do am TB qua HTTP POST moi 20s (chi 2 field)
        if i == 20:
            thingspeak_http(tb1, tb2)
            print("Đã gửi dữ liệu lên ThingSpeak qua HTTP thành công!")
            i = 0
            data1.clear()
            data2.clear()

if __name__ == '__main__':
    main()
