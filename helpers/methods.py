
def thread_runner(threads):
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

def split_list(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))