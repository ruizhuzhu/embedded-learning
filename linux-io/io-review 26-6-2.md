io复习 26/6/2
静态库与动态库
1.什么是库：就是一个可执行的代码的二进制形式。通俗说就是将一个用户写好的程序打包好，当其他用户或者其他模块使用时，只要有这个库文件就可以，不需要源代码，即一组预先编译好的方法集合

2.windows linux库文件的区别
win: .ddl lin:.so .a

3.动态库与静态库
静态：编译时载入代码，体积大（库里的所有代码复制到了程序中），运行速度快（因为编译时就已经加载了库），后续升级后 需要重新编译链接  .a后缀
动态：运行时载入代码，体积小（程序执行时才加载动态库），运行速度慢（每次运行都得加载），升级简单（升级动态库就行），移植性差。 .so后缀

4.动态静态库的制作与使用
静态库
   	1.将源代码文件编译为目标文件，不链接
	gcc -c xx.c -o xx.o
	2.制作库
	ar crs -libxxx.a  xxx为库名 xx.o ...o
	c:create 创建库
	r:replace 替换添加
	s:index添加索引
	3.使用静态库
	gcc xx.c -L. -l库名 或者 gcc xx.c libxxx.a 使用联合编译
动态库
	1.使用 -fPIC 创建与地址无关的编译程序
	gcc -fPIC xx.c -o xx.o
	2.创建共享库（动态库）
	gcc -shared -o libxxx.so xxx为库名 xxx.o ...o
	3.使用动态库
	gcc xxx.c -L. -l库名或者联合编译
	一般来说 不用指定库名，因为系统默认会到 /lib or /usr/lib下寻找所需库文件
如果出现	while loading shared libraries: libmyadd.so: cannot open shared object file: No such file or directory
有三种解决方式
1.将库自行拷贝到 /lib 和 /usr/lib目录下（永久）
2.设置环境变量：export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:（临时，当前终端有效）
3.配置 /etc/ld.so.conf（系统级）修改配置文件：在 /etc/ld.so.conf 中添加库路径，然后执行 sudo ldconfig（更新缓存）
补充：使用 ldd 可执行文件名 可以查看程序链接了哪些动态库。

5.Linux io的各类模型
	1.阻塞式IO：实现简单，不浪费CPU，但是只能处理一项任务 无法处理并行化场景
	2.非阻塞式IO：浪费CPU，不断轮询，可以同时处理多件事情
	3.信号驱动IO：不需要轮询，cpu占用低，且支持异步，十分高效。但是需要底层支持驱动

6.信号驱动的工作原理
	1.程序通过fcntl（fd,F_SETOWN,getpid()）来告诉系统内核，此进程我监管
	2.设置异步int flag = fcntl（fd,F_GETFL）; flag |= O_ASYNC;//异步 fcntl(fd,F_SETFL,flag);
	3.signal捕捉SIGIO信号 --- SIGIO:内核通知会进程有新的IO信号可用
		一旦内核给进程发送sigio信号，则执行handler处理函数
		    signal(SIGIO,handler);