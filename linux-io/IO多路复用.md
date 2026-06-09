### IO多路复用
##  1.io多路复用
#   select  poll    epoll
    1.1 select
    特点：一个进程最多监听1024个文件描述符
          select被唤醒后每次都要重新轮询
          每次都要清空未发生响应的文件描述符，且将其从用户空间拷贝到内核空间，效率低，开销大
    
    1.2 select的编程步骤
    以监控鼠标键盘事件为例子
    '#include <sys/time.h>
     #include <sys/types.h>
     #include <unistd.h>
     #include <stdio.h>
     #include <errno.h>
     #include <fcntl.h>
     #include <sys/stat.h>
     int main()
     {
        int fd = open("/dev/input/mouse",O_RDONLY);//鼠标的文件描述符
        if(fd<0)
        {
            perror("open mouse err!\n");
            return 0;
        }
        int ret = 0;//用于监听文件描述符表中事件的的响应
        char buf[1024];
        //构建文件描述符的表；
        fd_set rfds;
        while(1)//开始轮询
        {
            //清空表
            FD_ZERO(&rfds);
            //将关心的文件描述符添加到表中
            FD_SET(0,&rfds);//键盘
            FD_SET(fd,&rfds);//鼠标
            //select函数
            int max_fd = (fd > 0) ? fd : 0;
            ret = select(max_fd,&rfds,NULL,NULL,NULL);
            if(ret<0)
            {
                perror("select err");
                close(fd);
                return 0;
            }
            else if(ret == 0)
            {
                fprintf(stdout,"time out");
            }
            //如果有事件响应
            else
            {
                if(F_ISSET(0,&rfds))//键盘（标准输入）
                {
                    int n = read(0,buf,sizeof(buf))
                    if(n>0)
                    {
                        buf[n] = '\0';
                        printf("%s",buf);
                    }
                }
                if(F_ISSET(fd,&rfds))
                {
                    int n = read(fd, buf, sizeof(buf));
                    if(n > 0)
                    {
                        // 鼠标数据通常是3字节：状态 + X偏移 + Y偏移
                        printf("鼠标事件: ");
                        for(int i = 0; i < n; i++)
                        {
                            printf("%02X ", (unsigned char)buf[i]);
                        }
                        printf("\n");
                }
                }

            }

        }
        close(fd);
        return 0;
     }
    '