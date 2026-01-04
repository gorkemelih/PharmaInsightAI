// Translation dictionaries for TR/EN

export const dictionaries = {
    en: {
        // Navigation
        nav: {
            overview: "Overview",
            projects: "Projects",
            runs: "Runs",
            users: "Users",
            settings: "Settings",
        },
        // Dashboard
        dashboard: {
            title: "Dashboard",
            totalProjects: "Total Active Projects",
            papersAnalyzed: "Papers Analyzed",
            totalRuns: "Total Runs",
            pendingRuns: "Pending Runs",
            researchDirectory: "Research Run Directory",
            manageAnalyses: "Manage ongoing analyses and monitor progress.",
            export: "Export",
            newRun: "New Run",
            query: "QUERY",
            project: "PROJECT",
            papers: "PAPERS",
            status: "STATUS",
            created: "CREATED",
            actions: "ACTIONS",
            noRuns: "No runs yet. Create a project and start your first analysis!",
            refresh: "Refresh",
            inProgress: "In Progress",
        },
        // Status
        status: {
            completed: "Completed",
            running: "Running",
            pending: "Pending",
            failed: "Failed",
            done: "Done",
            queued: "Queued",
        },
        // Common
        common: {
            home: "Home",
            search: "Search",
            view: "View",
            back: "Back",
            save: "Save",
            cancel: "Cancel",
            create: "Create",
            delete: "Delete",
            loading: "Loading...",
            error: "Error",
        },
        // Topbar
        topbar: {
            searchPlaceholder: "Search projects, runs...",
            notifications: "Notifications",
            help: "Help",
        },
    },
    tr: {
        // Navigation
        nav: {
            overview: "Genel Bakış",
            projects: "Projeler",
            runs: "Analizler",
            users: "Kullanıcılar",
            settings: "Ayarlar",
        },
        // Dashboard
        dashboard: {
            title: "Kontrol Paneli",
            totalProjects: "Toplam Aktif Proje",
            papersAnalyzed: "Analiz Edilen Makale",
            totalRuns: "Toplam Analiz",
            pendingRuns: "Bekleyen Analiz",
            researchDirectory: "Araştırma Analiz Dizini",
            manageAnalyses: "Devam eden analizleri yönetin ve ilerlemeyi izleyin.",
            export: "Dışa Aktar",
            newRun: "Yeni Analiz",
            query: "SORGU",
            project: "PROJE",
            papers: "MAKALE",
            status: "DURUM",
            created: "OLUŞTURULMA",
            actions: "İŞLEMLER",
            noRuns: "Henüz analiz yok. Bir proje oluşturun ve ilk analizinizi başlatın!",
            refresh: "Yenile",
            inProgress: "Devam Ediyor",
        },
        // Status
        status: {
            completed: "Tamamlandı",
            running: "Çalışıyor",
            pending: "Beklemede",
            failed: "Başarısız",
            done: "Tamamlandı",
            queued: "Sırada",
        },
        // Common
        common: {
            home: "Ana Sayfa",
            search: "Ara",
            view: "Görüntüle",
            back: "Geri",
            save: "Kaydet",
            cancel: "İptal",
            create: "Oluştur",
            delete: "Sil",
            loading: "Yükleniyor...",
            error: "Hata",
        },
        // Topbar
        topbar: {
            searchPlaceholder: "Proje, analiz ara...",
            notifications: "Bildirimler",
            help: "Yardım",
        },
    },
} as const;

export type Locale = keyof typeof dictionaries;

// Use structural type for Dictionary to allow both locales
export type Dictionary = {
    nav: { overview: string; projects: string; runs: string; users: string; settings: string };
    dashboard: {
        title: string;
        totalProjects: string;
        papersAnalyzed: string;
        totalRuns: string;
        pendingRuns: string;
        researchDirectory: string;
        manageAnalyses: string;
        export: string;
        newRun: string;
        query: string;
        project: string;
        papers: string;
        status: string;
        created: string;
        actions: string;
        noRuns: string;
        refresh: string;
        inProgress: string;
    };
    status: { completed: string; running: string; pending: string; failed: string; done: string; queued: string };
    common: { home: string; search: string; view: string; back: string; save: string; cancel: string; create: string; delete: string; loading: string; error: string };
    topbar: { searchPlaceholder: string; notifications: string; help: string };
};
