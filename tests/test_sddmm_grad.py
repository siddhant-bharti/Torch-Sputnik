import torch
import torch_sputnik
from utils.util import *

class Sddmm(torch.autograd.Function):
    @staticmethod
    def forward(ctx, m, k, n, row_indices, row_offsets, column_indices, lhs_matrix, rhs_matrix):
        ctx.m = m
        ctx.k = k
        ctx.n = n
        ctx.row_indices = row_indices
        ctx.row_offsets = row_offsets
        ctx.column_indices = column_indices
        ctx.save_for_backward(lhs_matrix, rhs_matrix)
        return torch_sputnik.sddmm(m, n, row_indices, row_offsets, column_indices, lhs_matrix, rhs_matrix)

    @staticmethod
    def backward(ctx, grad_output):
        m = ctx.m
        k = ctx.k
        n = ctx.n
        row_indices = ctx.row_indices
        row_offsets = ctx.row_offsets
        column_indices = ctx.column_indices
        lhs_matrix, rhs_matrix = ctx.saved_tensors

        grad_m = grad_k =  grad_n = grad_row_indices = grad_row_offsets = grad_column_indices = grad_lhs = grad_rhs = None
        
        # lhs grad
        grad_lhs = torch_sputnik.spmm(m, k, n, grad_output, row_indices, row_offsets, column_indices, rhs_matrix)

        grad_t = grad_output.clone()
        row_offsets_t = row_offsets.clone()
        column_indices_t = column_indices.clone()

        torch_sputnik.csr_transpose(m, n, grad_output, row_offsets, column_indices, grad_t, row_offsets_t, column_indices_t)
        row_indices_t = diffsort(row_offsets_t).to(torch.int32)
        
        # rhs grad
        grad_rhs = torch_sputnik.spmm(n, k, m, grad_t, row_indices_t, row_offsets_t, column_indices_t, lhs_matrix)
        #print("dense matrix grad:")
        #print(out)

        return grad_m, grad_k, grad_n, grad_row_indices, grad_row_offsets, grad_column_indices, grad_lhs, grad_rhs

device = torch.device("cuda:0")  # Uncomment this to run on GPU

nnz = 64
m = 8
k = 8
n = 8
x = torch.arange(1, nnz + 1, dtype=torch.float32).view(m, k).cuda()
values, row_indices, row_offsets, column_indices = dense_to_sparse(x)

lhs = torch.arange(1, nnz + 1, dtype=torch.float32, device=device).view(k, n).cuda().requires_grad_()
rhs = torch.arange(1, nnz + 1, dtype=torch.float32, device=device).view(k, n).cuda().requires_grad_()

correct_result = torch.arange(1, nnz + 1, dtype=torch.float32, device=device).view(k, n).cuda()

# To apply our Function, we use Function.apply method. We alias this as 'P3'.
P3 = Sddmm.apply

# Forward pass: compute predicted y using operations; we compute
# P3 using our custom autograd operation.
y_pred = P3(m, k, n, row_indices, row_offsets, column_indices, lhs, rhs).view(m, n)

# Compute and print loss
print(y_pred - correct_result)
loss = (y_pred - correct_result).pow(2).sum()
print(loss.item())

# Use autograd to compute the backward pass.
loss.backward()
print(f'After: {lhs.grad}')
print(f'After: {rhs.grad}')
