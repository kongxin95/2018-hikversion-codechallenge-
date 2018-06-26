# 2018-hikversion-codechallenge-
2018 hikversion codechallenge，海康软件大赛
本届大赛试题以无人机AI对战为背景，参赛选手以自建队伍为单位，在给定地图的三维空间与其他限定条件下，进行运送货物的对战比赛，每场比赛中获得价值最多者获胜。
赛题链接：http://codechallenge.hikvision.com/topic_introd.aspx?k1=6
本次比赛不同于以往ACM，需要存在网络交互。参赛者的程序需要去链接服务器，（服务器IP，端口待定， 链接为长链接，中间不能关闭socket，否则认为失败），链接到服务器后， 服务器会发送地图信息给二个参赛者，发送地图信息后表示比赛开始，该时刻为0，参赛者程序收到地图信息，此时，参赛者不能移动无人机，不能充电；同时需要参赛者将他们所控制的无人机时刻为0的位置发送给服务器， 服务器接受到二个参赛者的信息后，做一些处理，并将信息合并分别发送给参赛者程序，此时时刻为1。同理参赛者需要将时刻为1的无人机等信息发送给服务器。以此类推， 直到比赛结束。具体发送数据格式见协议说明。

当比赛结束时，获得的价值最多者获胜（这里的价值包括现有无人机价值+剩余价值），如果价值相同，那么所有运行时间最短的获胜，（运行时间指 服务器每次发送给参数者信息到接收到信息这段时间总和）。
服务器发送给参赛者的json格式如下（赛题包中有相应的文件）：

参考https://cdn.acmcoder.com/assets/hikvision2018/droneaisocket.html#jump6

参赛者发送到服务器的json格式如下：

参考https://cdn.acmcoder.com/assets/hikvision2018/droneaisocket.html#jump5

关于Socket传输协议格式和JSON的示例，请参考：https://git.acmcoder.com/hikvision/UAVRobotSimple
