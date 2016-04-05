import numpy as np
import time
import scipy.optimize as op


def project_into_bounds(point, bounds):
    """
    Project the given point into the given bounds
    :param bounds:
    :param point:
    :return:
    """
    if bounds is None:
        return point
    low_bounds = [bound[0] for bound in bounds]
    high_bounds = [bound[1] for bound in bounds]
    proj = np.copy(point)
    i = 0
    for coord, l_bound, h_bound in list(zip(point, low_bounds, high_bounds)):
        if not(l_bound is None):
            if coord < l_bound:
                proj[i] = l_bound
        if not(h_bound is None):
            if coord > h_bound:
                proj[i] = h_bound
        i += 1
    return proj


def _linesearch_armiho(fun, point, gradient, bounds=None, step_0=1.0, theta=0.5, eps=1e-2,
                       direction=None, point_loss=None, maxstep=np.inf):
    """
    Line search using Armiho rule
    :param fun: function, being optimized or a tuple (function, gradient)
    :param point: the point of evaluation
    :param direction: direction of the optimization
    :param gradient: gradient at the point point
    :param step_0: initial step length
    :param theta: theta parameter for updating the step length
    :param eps: parameter of the armiho rule
    :param point_loss: fun value at the point point
    :return: (new point, step) — a tuple, containing the chosen step length and
    the next point for the optimization method
    """
    if point_loss is None:
        current_loss = fun(point)
    else:
        current_loss = point_loss
    if direction is None:
        direction = -gradient

    step = step_0/theta
    while step > maxstep:
        step *= theta
    new_point = point + step * direction
    new_point = project_into_bounds(new_point, bounds)
    while fun(new_point) > current_loss + eps * step * direction.dot(gradient):
        step *= theta
        new_point = point + step * direction
        new_point = project_into_bounds(new_point, bounds)
    return new_point, step


def gradient_descent(oracle, point, bounds=None, options=None):
    """
    Gradient descent optimization method
    :param oracle: oracle function, returning the function value and it's gradient, given point
    :param point: point
    :param bounds: bounds on the variables
    :param options: a dictionary, containing the following fields
        'maxiter': maximum number of iterations
        'verbose': a boolean, showing weather or not to print the convergence info
        'print_freq': the frequency of the convergence messages
        'g_tol': the tolerance wrt gradient. If the gradient at the current point is
        smaller than the tollerance, the method stops
        'step_tol' the tolerance wrt the step length. If the step length at current
        iteration is less than tollerance, the method stops.
        'maxstep' is the maximum allowed step length
    default options: {'maxiter': 1000, 'print_freq':10, 'verbose': False, 'g_tol': 1e-5, 'step_tol': 1e-16,
                       'maxstep': 1.0}
    :return: the point with the minimal function value found
    """
    defaul_options = {'maxiter': 1000, 'print_freq':10, 'verbose': False, 'g_tol': 1e-5, 'step_tol': 1e-16,
                       'maxstep': 1.0}
    defaul_options.update(options)
    if 'print_freq' in options.keys():
        defaul_options['verbose'] = True
    options = defaul_options

    step = 1.0
    x = point
    loss_fun = lambda w: oracle(w)[0]
    x_lst = [np.copy(x)]
    time_lst = [0]
    start = time.time()

    for i in range(options['maxiter']):
        x = project_into_bounds(x, bounds)
        loss, grad = oracle(x)
        if np.linalg.norm(grad) < options['g_tol']:
            if options['verbose']:
                print("Gradient norm reached the stopping criterion")
            break
        x, step = _linesearch_armiho(fun=loss_fun, gradient=grad, point_loss=loss, bounds=bounds, point=x,
                                     step_0=step, maxstep=options['maxstep'])
        x_lst.append(np.copy(x))
        time_lst.append(time.time() - start)
        if step < options['step_tol']:
            if options['verbose']:
                print("Step length reached the stopping criterion")
            break
        if not (i % options['print_freq']) and options['verbose']:
            print("Iteration ", i, ":")
            print("\tGradient norm", np.linalg.norm(grad))
            print("\tFunction value", loss)
    return x, x_lst, time_lst


def stochastic_gradient_descent(oracle, point, n, bounds=None, options=None):
    """
    Stochastic gradient descent optimization method for finite sums
    :param oracle: an oracle function, returning the gradient approximation by one data point,
    given it's index and the point
    :param point:
    :param n: number of training examples
    :param bounds: bounds on the variables
    :param options: a dictionary, containing the following fields
        'maxiter': maximum number of iterations
        'verbose': a boolean, showing weather or not to print the convergence info
        'print_freq': the frequency of the convergence messages
        'batch_size': the size of the mini-batch, used for gradient estimation
        'step0': initial step of the method
        'gamma': a parameter of the step length rule. It should be in (0.5, 1). The smaller it
        is, the more aggressive the method is
        'update_rate': the rate of shuffling the data points
    defaul options: {'maxiter': 1000, 'print_freq':10, 'verbose': False, 'batch_size': 1,
                      'step0': 0.1, 'gamma': 0.55, 'update_rate':1}
    :return: optimal point
    """
    defaul_options = {'maxiter': 1000, 'print_freq':10, 'verbose': False, 'batch_size': 1,
                      'step0': 0.1, 'gamma': 0.55, 'update_rate':1}
    defaul_options.update(options)
    if 'print_freq' in options.keys():
        defaul_options['verbose'] = True
    options = defaul_options

    batch_size = options['batch_size']
    step0 = options['step0']
    gamma = options['gamma']

    batch_num = int(n / batch_size)
    if n % batch_size:
        batch_num += 1
    update_rate = options['update_rate']

    indices = np.random.random_integers(0, n-1, (update_rate * batch_num * batch_size,))
    step = step0
    x = point
    x = project_into_bounds(x, bounds)
    x_lst = [np.copy(x)]
    time_lst = [0]
    start = time.time()
    for epoch in range(options['maxiter']):
        for batch in range(batch_num):
            new_indices = indices[range(batch_size*batch, (batch + 1)*batch_size)]
            grad = oracle(x, new_indices)
            x -= grad * step
            x = project_into_bounds(x, bounds)
        x_lst.append(np.copy(x))
        time_lst.append(time.time() - start)

        if not (epoch % update_rate):
            indices = np.random.random_integers(0, n-1, (update_rate * batch_num * batch_size,))

        if not (epoch % options['print_freq']) and options['verbose']:
            print("Epoch ", epoch, ":")
            print("\tStep:", step)
            print("\tParameters", x[:2])
        step = step0 / np.power((epoch+1), gamma)
    return x, x_lst, time_lst


def check_gradient(oracle, point, print_diff=False):
    """
    Prints the gradient, calculated with the provided function
    and approximated via a finite difference.
    :param oracle: a function, returning the loss and it's grad given point
    :param point: point of calculation
    :param print_diff: a boolean. If true, the method prints all the entries of the true and approx.
    gradients
    :return:
    """
    fun, grad = oracle(point)
    app_grad = np.zeros(grad.shape)
    if print_diff:
        print('Approx.\t\t\t\t Calculated')
    for i in range(point.size):

        point_eps = np.copy(point)
        point_eps[i] += 1e-6
        app_grad[i] = (oracle(point_eps)[0] - fun) * 1e6
        if print_diff:
            print(app_grad[i], '\t', grad[i])
    print('\nDifference between calculated and approximated gradients')
    print(np.linalg.norm(app_grad.reshape(-1) - grad.reshape(-1)))


def stochastic_average_gradient(oracle, point, n, bounds=None, options=None):
    """
    Stochastic average gradient (SAG) optimization method for finite sums
    :param oracle: an oracle function, returning the gradient approximation by one data point,
    given it's index and the point
    :param point:
    :param n: number of training examples
    :param bounds: bounds on the variables
    :param options: a dictionary, containing the following fields
        'maxiter': maximum number of iterations
        'verbose': a boolean, showing weather or not to print the convergence info
        'print_freq': the frequency of the convergence messages
        'batch_size': the size of the mini-batch, used for gradient estimation
        'step0': initial step of the method
        'gamma': a parameter of the step length rule. It should be in (0.5, 1). The smaller it
        is, the more aggressive the method is
    defaul options: {'maxiter': 1000, 'print_freq':10, 'verbose': False, 'batch_size': 1,
                      'step0': 0.1, 'gamma': 0.55}
    :return: optimal point
    """
    defaul_options = {'maxiter': 1000, 'print_freq':10, 'verbose': False, 'batch_size': 1,
                      'step0': 0.1, 'gamma': 0.55}
    defaul_options.update(options)
    if 'print_freq' in options.keys():
        defaul_options['verbose'] = True
    options = defaul_options

    batch_size = options['batch_size']
    l = 1.0
    eps = 0.5

    def update_lipschitz_const (l, point, cur_loss=None, cur_grad=None):
        if cur_loss is None or cur_grad is None:
            cur_loss, cur_grad = batch_oracle(point)
        l *= np.power(2.0, - 1 / batch_oracle.batch_num)
        if l <= 1:
            l = 1
        new_point = point - cur_grad / l
        new_point = project_into_bounds(new_point, bounds)
        new_loss, _ = batch_oracle(new_point)

        while new_loss > cur_loss - eps * cur_grad.T.dot(cur_grad) / l:
            l *= 2
            new_point = point - cur_grad / l
            new_point = project_into_bounds(new_point, bounds)
            new_loss, _ = batch_oracle(new_point)
            if l > 1e16:
                print('Abnormal termination in linsearch')
                return 0
        return l

    class BatchOracle:
        def __init__(self, n, batch_size):
            self.num_funcs = n
            self.batch_size = batch_size
            self.batch_num = int(n / batch_size)
            if n % batch_size:
                self.batch_num += 1
            self.gradients = np.zeros((self.batch_num, point.size))
            self.current_grad = np.zeros(point.shape)
            self.cur_index = 0
            self.cur_batch_index = 0

        def update_gradients(self, new_grad):
            self.current_grad += (new_grad - self.gradients[self.cur_batch_index].reshape(point.shape)) / self.batch_num
            self.gradients[self.cur_batch_index] = new_grad.reshape(point.shape[0], )
            self.cur_index += batch_size
            self.cur_batch_index += 1
            if self.cur_batch_index > self.batch_num - 1:
                self.cur_index = 0
                self.cur_batch_index = 0
            return self.current_grad

        def __call__(self, eval_point):
            if self.cur_index + self.batch_size < n:
                indices = range(self.cur_index, self.cur_index + self.batch_size)
            else:
                indices = list(range(self.cur_index, n-1)) + list(range(self.cur_index + self.batch_size - n + 1))

            new_loss, new_grad = oracle(eval_point, indices)
            return new_loss, new_grad

    x = point
    x = project_into_bounds(x, bounds)
    batch_oracle = BatchOracle(n=n, batch_size=batch_size)
    x_lst = [np.copy(x)]
    time_lst = [0]
    start = time.time()

    for epoch in range(options['maxiter']):
        for i in range(batch_oracle.batch_num):
            loss, grad = batch_oracle(x)
            l = update_lipschitz_const(l, x, cur_loss=loss, cur_grad=grad)
            direction = batch_oracle.update_gradients(grad)
            if l == 0:
                return x
            x -= direction /(16 * l)
            x = project_into_bounds(x, bounds)
        x_lst.append(np.copy(x))
        time_lst.append(time.time() - start)
        if not (epoch % options['print_freq']) and options['verbose']:
            print("Epoch ", epoch, ":")
            print("\tLipschitz constant estimate:", l)
            print("\t", x[:2])    # print(x_lst)
    return x, x_lst, time_lst


def minimize_wrapper(func, x0, mydisp=False, jac=True, **kwargs):

    aux = {'start': time.time(), 'total': 0., 'it': 0}

    def callback(w):
        aux['total'] += time.time() - aux['start']
        if mydisp:
            print("Hyper-parameters at iteration", aux['it'], ":", w)
        time_list.append(aux['total'])
        w_list.append(np.copy(w))
        aux['it'] += 1
        aux['start'] = time.time()
    w_list = []
    time_list = []
    callback(x0)

    out = op.minimize(func, x0, jac=jac, callback=callback, **kwargs)

    return out, w_list, time_list