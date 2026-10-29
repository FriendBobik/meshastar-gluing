#include <iostream>
#include <mach/mach.h>
#include <mach/thread_policy.h>
#include <pthread.h>
int main() {
 thread_affinity_policy_data_t p={1};
 auto thread=mach_thread_self();
 auto ret=thread_policy_set(thread,THREAD_AFFINITY_POLICY,(thread_policy_t)&p,THREAD_AFFINITY_POLICY_COUNT);
 std::cout<<"affinity_policy_result="<<ret<<" ("<<mach_error_string(ret)<<")\n";
 mach_port_deallocate(mach_task_self(),thread);
 auto q=pthread_set_qos_class_self_np(QOS_CLASS_USER_INITIATED,0);
 std::cout<<"qos_user_initiated_result="<<q<<"\n";
}
