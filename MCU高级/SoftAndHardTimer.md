### 软件/硬件定时器
##  软件定时器
#   操作接口
``` c
    osTimerId_t osTimerNew(osTimerFunc_t func, osTimerType_t type,  void *argument, const osTimerAttr_t *attr);
    /*参数：
        func: 该函数指针用于指定在定时器到期时执行的回调函数， 当定时器触发，会执行该函数
            //typedef void (*osTimerFunc_t) (void *argument);
        type:定时器的类型，可选择 单次 或 循环触发
            /*  typedef enum {
                  /** 一次性定时器 **/
                  osTimerOnce   = 0,
                  /** 重复使用的定时器 **/
                  osTimerPeriodic  = 1
                } osTimerType_t;
        argument：传入定时器的回调函数的指针，当定时器到期，回调函数将接收到此函数，不需要NULL
        attr:定时器对象指针(见下面2)，用于指向特定的定时器属性，比如优先级，名称等，不需要为NULL
    */
    osStatus_t osTimerStart(osTimerId_t timer_id, uint32_t ticks);
    /*参数：
       timer_id：定时器ID，用于指定要启动的定时器，通常需要先使用osTimerNew函数创建定时器对象
       ticks: 设置的定时值  ms为单位
           返回值：
        成功返回0，失败返回错误码（错误码<0）
        关于错误码的定义：
            typedef enum {
                  osOK       =  0,          ///定时器成功启动
                  osError   = -1,           ///定时器发生错误，未能成功启动
                  osErrorTimeout   = -2,    ///超时错误
              osErrorResource  = -3,         ///资源不可用
              osErrorParameter   = -4,         ///参数错误
              osErrorNoMemory  = -5,         ///系统内存不足:无法为操作分配或保留内存。
    } osStatus_t;
    */
    osStatus_t osTimerStop (osTimerId_t timer_id);
    /*
    功能  ：停止定时器
  参数  ：timer_id：要停止的定时器ID
  返回值  ：操作状态
    */
    osStatus_t osTimerDelete (osTimerId_t timer_id);
    /*
    功能  ：删除定时器并释放资源
  参数  ：timer_id：要删除的定时器ID
  返回值  ：操作状态
    */
    uint32_t osTimerIsRunning (osTimerId_t timer_id);
    /*
    功能  ：检查定时器是否正在运行
  参数  ：timer_id：要检查的定时器ID
  返回值  ：0表示未运行，非0表示正在运行
    */
```
#   特点
    1.精度有限，1个tick 大约1-10ms
    2.微秒级时钟无法做到
    3.数量理论上无限，只要硬件内存足够大
    4.抖动大，如果系统繁忙，回调函数可能被阻塞
    5.操作简单：简单的api调动
##  硬件定时器
#   工作原理
    MCU 片内外设定时器（TIM1~TIMx），依赖于独立的时钟源
#   特点
    1.精度极高，微秒级甚至纳秒级
    2.CPU负载高时也能正常工作计时，独立于CPU
    3.需要硬件资源支持
    4.回调函数在ISR中执行，会中断上下文执行
    5.抖动小
    6.操作复杂：针对寄存器的位操作

##  使用场景
    LED闪烁 / 超时检测  软件定时器 / osDelay
    PWM（舵机/电机）    硬件 TIM
    输入捕获 / 测频     硬件 TIM
    μs 级精确延时       硬件 TIM（或 DWT）
    周期性业务任务      软件定时器 + 信号量