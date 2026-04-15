if(NOT TARGET hermes-engine::hermesvm)
add_library(hermes-engine::hermesvm SHARED IMPORTED)
set_target_properties(hermes-engine::hermesvm PROPERTIES
    IMPORTED_LOCATION "C:/Users/takeg/.gradle/caches/8.13/transforms/8a2cfaa69ecf999d20286b2ca1d7508e/transformed/hermes-android-250829098.0.9-debug/prefab/modules/hermesvm/libs/android.armeabi-v7a/libhermesvm.so"
    INTERFACE_INCLUDE_DIRECTORIES "C:/Users/takeg/.gradle/caches/8.13/transforms/8a2cfaa69ecf999d20286b2ca1d7508e/transformed/hermes-android-250829098.0.9-debug/prefab/modules/hermesvm/include"
    INTERFACE_LINK_LIBRARIES ""
)
endif()

