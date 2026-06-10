### 消息队列（RTOS）
##  CMSIS函数接口
```c
    osMessageQueueId_t osMessageQueueNew(uint32_t msg_count,uint32_t msg_size,const osMessageQueueAttr_t * attr);
/*
该函数创建并初始化一个消息队列对象。该函数的参数及返回值说明如下：
    msg_count ：队列中消息的最大数量。（队列的长度）
    msg_size ：消息的最大大小（以字节为单位）。
    attr ：消息队列属性。NULL：使用默认值。
返回值：
     队列的 ID，供其他函数引用；如果发生错误，则返回 NULL。
*/
osStatus_t 	osMessageQueuePut (osMessageQueueId_t mq_id,const void *msg_ptr, uint8_t msg_prio,uint32_t timeout);
osStatus_t 	osMessageQueueGet (osMessageQueueId_t mq_id, void *msg_ptr, uint8_t *msg_prio, 
uint32_t timeout);
/*
    mq_id是队列的变量名，即我们定义的QueueUartByteHandle；
    msg_ptr是要入队/出队的数据块指针；
    msg_prio比较奇怪，入队和出队对应的变量类型不同，表示优先级，但一般都赋NULL；
最后的timeout，不等待就为0，永远等待用osWaitForever。这两个函数都可以在中断中运行(timeout写0)。
*/
```
