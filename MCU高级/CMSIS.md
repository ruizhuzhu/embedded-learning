### CMSIS
##  CMSIS结构
    微控制器软件接口标准 (CMSIS) 是 Cortex-M 处理器系列的与供应商无关的硬件抽象层。CMSIS 可实现与处理器和外设之间的一致且简单的软件接口，从而简化软件的重用。

    CMSIS 包含以下组件：
    CMSIS-CORE：提供与 Cortex-M0、Cortex-M3、Cortex-M4、SC000 和 SC300 处理器与外围寄存器之间的接口
    CMSIS-DSP：包含以定点（分数 q7、q15、q31）和单精度浮点（32 位）实现的 60 多种函数的 DSP 库
    CMSIS-RTOS API：用于线程控制、资源和时间管理的实时操作系统的标准化编程接口
    CMSIS-SVD：包含完整微控制器系统（包括外设）的程序员视图的系统视图描述 XML 文件
### 同步与互斥
##  同步
    进程同步是指多个进程中发生的事件存在某种时序关系，必须协同动作共同完成一个任务。
#   volatile
    volatile是 C/C++ 中的一个类型修饰符， 强制编译器每次访问变量时都从内存中读取，而非使用寄存器中的缓存值。这会禁止编译器对变量访问的优化。使用其会导致性能开销变大，降低执行效率
    用于告诉编译器：被修饰的变量可能会被程序本身之外的因素意外改变。
    例如：​内存映射的I/O端口，值可能由硬件改变，变量进行循环计数时，优化会导致计数错误。

##  互斥
    多个任务在运行过程中，都需要某一个资源时，它们便产生了竞争关系，它们可能竞争某一块内存空间，也 可能竞争某一个IO设备。当一方获取资源时，其他任务只能在该任务释放资源之后 才能去访问该资源，这就是任务互斥。
#   通过信号量实现互斥
    信号量是实现任务互斥的经典机制。它的本质是一个非负整数计数器，配合两个原子操作（P/V操作）来管理资源的访问权。
    信号量来代表某一种临界资源，值表示该资源的数量
    如果型好靓的值只为0，1，则该信号量又被称为二进制信号量，其通过计数值加一 为“give”让出资源；计数值减一 为“take”占用资源。
    相关的一些CMSIS接口函数
    c
    osSemaphoreId_t osSemaphoreNew(uint32_t max_count, 
                               uint32_t initial_count, 
                               const osSemaphoreAttr_t *attr);
    //创建信号量，参数为 最大计数值，该信号量的初始值，信号量的属性
    //返回值成功：返回信号量的 ID，失败 NULL
    osStatus_t osSemaphoreAcquire(osSemaphoreId_t semaphore_id, uint32_t timeout);
    //申请信号量，参数为 申请占用信号量的句柄，超时检测
    //返回值：
    osOK: 成功获取信号量。
    osErrorTimeout: 在指定的超时时间内未获取到信号量。
    osErrorResource: 如果timeout=0时信号量不可用。
    osErrorParameter: 参数错误，比如semaphore_id无效。
    osErrorISR: 在中断服务程序中调用，但该信号量不允许在ISR中使用（注意：有些实现可能允许在ISR中使用，但通常需要特定的函数版本）。

    osStatus_t osSemaphoreRelease(osSemaphoreId_t semaphore_id);
    //释放信号量，参数为 申请释放信号量的句柄
    //返回值：
    osOK: 成功释放信号量。
    osErrorResource: 信号量计数已经达到最大值（无法再增加）。
    osErrorParameter: 参数错误，semaphore_id无效。
    osErrorISR: 在中断服务程序中调用，但该信号量不允许在ISR中释放（同样，有些实现可能有ISR安全版本）。
#   通过互斥量实现互斥
    互斥量是专门为实现互斥访问而设计的同步原语，与二进制信号量相比，它增加了所有权和优先级继承等特性。
    相关CMSIS接口函数
        osMutexId_t osMutexNew(const osMutexAttr_t *attr);
    功能：创建新的互斥锁对象
    参数：
    attr：指向互斥锁属性的指针（可为 NULL 使用默认属性）
    返回值：
        成功：互斥锁 ID
        失败：NULL
    属性结构体 osMutexAttr_t：
        typedef struct {
        const char          *name;      // 互斥锁名称（调试用）
        uint32_t            attr_bits;  // 属性位（见下方标志）
        void                *cb_mem;    // 控制块内存（通常为NULL）
        uint32_t            cb_size;    // 控制块大小
        } osMutexAttr_t;
    属性位标志：
        osMutexRecursive：创建递归互斥锁
        osMutexPrioInherit：启用优先级继承（防止优先级反转）
        osMutexRobust：强健互斥锁（FreeRTOS 不支持此特性）

        osStatus_t osMutexAcquire(osMutexId_t mutex_id, uint32_t timeout);
    功能：获取互斥锁所有权
    参数：
    mutex_id：互斥锁 ID
    timeout：超时时间（单位：tick）
    0：不等待，立即返回
    osWaitForever：无限期等待
    n：等待 n 个 tick
    返回值：
    osOK：成功获取锁
    osErrorTimeout：超时未获取
    osErrorResource：锁不可用（timeout=0时）
    osErrorParameter：参数错误
    osStatus_t osMutexRelease(osMutexId_t mutex_id);
    功能：释放互斥锁所有权
    参数：互斥锁 ID
    返回值：
    osOK：成功释放
    osErrorResource：当前任务不持有锁
    osErrorParameter：参数错误
    osStatus_t osMutexDelete(osMutexId_t mutex_id);
    功能：删除互斥锁并释放资源
    参数：互斥锁 ID
    返回值：
    osOK：成功删除
    osErrorParameter：参数错误
    osErrorResource：锁仍被占用
    osThreadId_t osMutexGetOwner(osMutexId_t mutex_id);
    功能：获取当前持有互斥锁的任务 ID
    参数：互斥锁 ID
    返回值：
    持有锁的任务 ID
    NULL：无任务持有或参数错误

##  优先级反转与优先级继承
    优先级反转：高优先级任务因低优先级任务持有共享资源而被阻塞，反而被中等优先级任务抢占的现象。
    优先级继承：当低优先级任务阻塞了高优先级任务时，临时将低优先级任务的优先级提升到与高优先级相同，使其尽快释放资源。释放资源后恢复其原有优先级。

