source_filename = "mellow-synthetic-affine.metal"
target datalayout = "e-p:64:64:64-i1:8:8-i8:8:8-i16:16:16-i32:32:32-i64:64:64-f32:32:32-f64:64:64-v16:16:16-v24:32:32-v32:32:32-v48:64:64-v64:64:64-v96:128:128-v128:128:128-v192:256:256-v256:256:256-v512:512:512-v1024:1024:1024-n8:16:32"
target triple = "air64_v27-apple-macosx15.6.0"
define weak_odr void @air_affine(ptr addrspace(1) noundef %data, i32 noundef %gid) {
entry:
  %index = zext i32 %gid to i64
  %element = getelementptr inbounds i32, ptr addrspace(1) %data, i64 %index
  %input = load i32, ptr addrspace(1) %element, align 4
  %scaled = mul i32 %input, 7
  %output = add i32 %scaled, 3
  store i32 %output, ptr addrspace(1) %element, align 4
  ret void
}
!air.kernel = !{!0}
!air.version = !{!5}
!air.language_version = !{!6}
!0 = !{ptr @air_affine, !1, !2}
!1 = !{}
!2 = !{!3, !4}
!3 = !{i32 0, !"air.buffer", !"air.location_index", i32 0, i32 1, !"air.read_write", !"air.address_space", i32 1, !"air.arg_type_size", i32 4, !"air.arg_type_align_size", i32 4, !"air.arg_type_name", !"uint", !"air.arg_name", !"data"}
!4 = !{i32 1, !"air.thread_position_in_grid", !"air.arg_type_name", !"uint", !"air.arg_name", !"gid"}
!5 = !{i32 2, i32 7, i32 0}
!6 = !{!"Metal", i32 3, i32 2, i32 0}
