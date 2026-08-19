# Светлана v13 integration

Светлана объединена с Web и Flutter-частью «Мира Самозанятых».

- Web: `frontend/public/svetlana/`
- Flutter: `mobile/assets/svetlana/`
- Backend: `app/api/svetlana.py`
- Web UI: `frontend/src/components/SvetlanaAvatar.tsx`, `frontend/src/pages/Svetlana.tsx`
- Mobile UI: `mobile/lib/presentation/widgets/common/svetlana_avatar_view.dart`, `mobile/lib/presentation/screens/svetlana/svetlana_screen.dart`

Полная модель v13 присутствует в интегрированном пакете и проверена по размеру, структуре GLB и SHA-256. При этом facial rig сам описывает себя как procedural scaffold, поэтому это не следует выдавать за финальную DCC-production facial rig без отдельной визуальной проверки на устройстве.
