#include <stdio.h>          // 标准输入输出
#include <stdlib.h>         // 标准库函数
#include <sys/epoll.h>      // epoll相关函数和结构体
#include <unistd.h>         // Unix标准函数
#include <string.h>         // 字符串处理
#include <fcntl.h>          // 文件控制（用于设置非阻塞）
#include <errno.h>          // 错误号定义

#define BUFFER_SIZE 1024    // 缓冲区大小
#define MAX_EVENTS 10       // 每次epoll_wait返回的最大事件数
#define TIMEOUT 5000        // 超时时间5秒

// 设置文件描述符为非阻塞模式的辅助函数
int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);  // 获取当前文件描述符标志
    if (flags == -1) return -1;         // 获取失败
    // 设置非阻塞标志：O_NONBLOCK
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

int main() {
    int epoll_fd, nfds;                 // epoll文件描述符和就绪事件数
    struct epoll_event ev, events[MAX_EVENTS];  // 事件结构体
    char buffer[BUFFER_SIZE];           // 数据缓冲区
    
    // 创建epoll实例
    // epoll_create1(0) 创建epoll实例，参数0表示使用默认标志
    // 返回epoll文件描述符，失败返回-1
    epoll_fd = epoll_create1(0);
    if (epoll_fd == -1) {
        perror("epoll_create1");
        exit(EXIT_FAILURE);
    }
    
    // 将标准输入设置为非阻塞模式
    // 边缘触发(ET)模式必须使用非阻塞I/O
    if (set_nonblocking(STDIN_FILENO) == -1) {
        perror("fcntl");
        exit(EXIT_FAILURE);
    }
    
    // 配置要监听的事件
    ev.events = EPOLLIN | EPOLLET;  // 监听可读事件，使用边缘触发(ET)模式
    // EPOLLIN: 可读事件
    // EPOLLET: 边缘触发模式（Edge Triggered）
    // 水平触发模式使用 EPOLLIN
    ev.data.fd = STDIN_FILENO;  // 将文件描述符保存在事件数据中
    
    // 将标准输入添加到epoll实例中
    // EPOLL_CTL_ADD: 添加文件描述符到epoll实例
    // 参数: epoll_fd, 操作类型, 要添加的fd, 事件配置
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, STDIN_FILENO, &ev) == -1) {
        perror("epoll_ctl: stdin");
        exit(EXIT_FAILURE);
    }
    
    printf("epoll示例 - 边缘触发模式\n");
    
    // 主事件循环
    while (1) {
        printf("等待事件...\n");
        
        // 等待事件发生
        // epoll_wait: 等待就绪的事件
        // 参数: epoll_fd, 事件数组, 最大事件数, 超时时间(毫秒)
        // 返回: 就绪的事件数量，0表示超时，-1表示错误
        nfds = epoll_wait(epoll_fd, events, MAX_EVENTS, TIMEOUT);
        
        if (nfds == -1) {       // 出错
            perror("epoll_wait");
            break;
        } else if (nfds == 0) { // 超时
            printf("超时\n");
            continue;
        }
        
        // 处理所有就绪的事件
        for (int i = 0; i < nfds; i++) {
            // 检查是哪个文件描述符就绪
            if (events[i].data.fd == STDIN_FILENO) {
                // 边缘触发模式必须一次性读取所有可用数据
                // 否则剩余数据不会再次触发事件
                while (1) {  // 循环读取直到没有数据
                    memset(buffer, 0, BUFFER_SIZE);  // 清空缓冲区
                    
                    // 从标准输入读取数据
                    int n = read(STDIN_FILENO, buffer, BUFFER_SIZE - 1);
                    
                    if (n > 0) {  // 成功读取到数据
                        buffer[n] = '\0';  // 添加字符串结束符
                        printf("收到数据: %s", buffer);
                    } else if (n == 0) {  // 读到文件结束符(EOF)
                        printf("输入结束\n");
                        break;  // 退出读取循环
                    } else {  // 读取出错
                        // 检查是否是"没有数据可读"的错误
                        if (errno == EAGAIN || errno == EWOULDBLOCK) {
                            // 这是期望的情况：已读取所有数据
                            break;  // 退出读取循环
                        }
                        perror("read");  // 其他错误
                        break;
                    }
                }
            }
        }
    }
    
    // 关闭epoll实例
    close(epoll_fd);
    return 0;
}