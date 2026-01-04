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
        // Projects
        projects: {
            title: "Projects",
            subtitle: "Manage your research projects",
            newProject: "New Project",
            noProjects: "No projects yet",
            createFirst: "Create your first project to start analyzing literature",
            createModalTitle: "Create Project",
            deleteConfirmation: "Are you sure you want to delete this project? This will also delete all its analysis runs.",
            name: "Name",
            description: "Description (optional)",
            placeholderName: "My Research Project",
            placeholderDesc: "Describe the research focus...",
            deleteTooltip: "Delete project",
        },
        // Run Details
        run: {
            backToProject: "Back to Project",
            downloadPdf: "Download PDF",
            generating: "Generating...",
            query: "Research Query",
            tabs: {
                papers: "Papers",
                summary: "Run Summary",
                claims: "Claims Draft",
            },
            status: {
                waiting: "Waiting in queue...",
                searching: "Searching literature databases...",
                found: "Found {n} papers",
                failed: "Analysis failed",
            },
            progress: {
                title: "AI Analysis Progress",
                analyzed: "{n}/{total} analyzed",
                processing: "Processing...",
                synthesizing: "Synthesizing findings...",
            },
            papers: {
                title: "Papers Found",
                noPapers: "No papers found.",
                table: {
                    title: "Title",
                    year: "Year",
                    aiStatus: "AI Status",
                    actions: "Actions",
                },
                viewSummary: "View Summary",
                generateSummary: "Generate Summary",
            },
            summary: {
                title: "Run Summary",
                waiting: "Waiting for paper analysis to complete...",
                failed: "Synthesis failed",
                tldr: "Executive Summary (TLDR)",
                consensus: "Consensus Level",
                keyPoints: "Key Points",
                gaps: "Research Gaps",
                references: "References",
                noSummary: "No summary available.",
            },
            claims: {
                title: "Claims Draft",
                noClaims: "No claims generated yet.",
            },
            details: {
                title: "Details",
                created: "Created",
                runId: "Run ID",
            },
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
        time: {
            minsAgo: "{n} min ago",
            hoursAgo: "{n} hrs ago",
            daysAgo: "{n} days ago",
            justNow: "Just now",
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
        // Projects
        projects: {
            title: "Projeler",
            subtitle: "Araştırma projelerinizi yönetin",
            newProject: "Yeni Proje",
            noProjects: "Henüz proje yok",
            createFirst: "Literatür analizine başlamak için ilk projenizi oluşturun",
            createModalTitle: "Proje Oluştur",
            deleteConfirmation: "Bu projeyi silmek istediğinize emin misiniz? Bu işlem, projeye ait tüm analizleri de silecektir.",
            name: "İsim",
            description: "Açıklama (isteğe bağlı)",
            placeholderName: "Araştırma Projem",
            placeholderDesc: "Araştırma konusunu tanımlayın...",
            deleteTooltip: "Projeyi sil",
        },
        // Run Details
        run: {
            backToProject: "Projeye Dön",
            downloadPdf: "PDF İndir",
            generating: "Oluşturuluyor...",
            query: "Araştırma Sorgusu",
            tabs: {
                papers: "Makaleler",
                summary: "Analiz Özeti",
                claims: "İddia Taslağı",
            },
            status: {
                waiting: "Sırada bekliyor...",
                searching: "Literatür taranıyor...",
                found: "{n} makale bulundu",
                failed: "Analiz başarısız",
            },
            progress: {
                title: "Yapay Zeka Analiz İlerlemesi",
                analyzed: "{n}/{total} analiz edildi",
                processing: "İşleniyor...",
                synthesizing: "Bulgular sentezleniyor...",
            },
            papers: {
                title: "Bulunan Makaleler",
                noPapers: "Makale bulunamadı.",
                table: {
                    title: "Başlık",
                    year: "Yıl",
                    aiStatus: "YZ Durumu",
                    actions: "İşlemler",
                },
                viewSummary: "Özeti Gör",
                generateSummary: "Özet Oluştur",
            },
            summary: {
                title: "Analiz Özeti",
                waiting: "Makale analizinin tamamlanması bekleniyor...",
                failed: "Sentez başarısız",
                tldr: "Yönetici Özeti (TLDR)",
                consensus: "Konsensüs Düzeyi",
                keyPoints: "Ana Noktalar",
                gaps: "Araştırma Boşlukları",
                references: "Referanslar",
                noSummary: "Özet mevcut değil.",
            },
            claims: {
                title: "İddia Taslağı",
                noClaims: "Henüz iddia oluşturulmadı.",
            },
            details: {
                title: "Detaylar",
                created: "Oluşturulma",
                runId: "Analiz ID",
            },
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
        time: {
            minsAgo: "{n} dk önce",
            hoursAgo: "{n} sa önce",
            daysAgo: "{n} gün önce",
            justNow: "Az önce",
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
    projects: {
        title: string;
        subtitle: string;
        newProject: string;
        noProjects: string;
        createFirst: string;
        createModalTitle: string;
        deleteConfirmation: string;
        name: string;
        description: string;
        placeholderName: string;
        placeholderDesc: string;
        deleteTooltip: string;
    };
    time: {
        minsAgo: string;
        hoursAgo: string;
        daysAgo: string;
        justNow: string;
    };
    run: {
        backToProject: string;
        downloadPdf: string;
        generating: string;
        query: string;
        tabs: {
            papers: string;
            summary: string;
            claims: string;
        };
        status: {
            waiting: string;
            searching: string;
            found: string;
            failed: string;
        };
        progress: {
            title: string;
            analyzed: string;
            processing: string;
            synthesizing: string;
        };
        papers: {
            title: string;
            noPapers: string;
            table: {
                title: string;
                year: string;
                aiStatus: string;
                actions: string;
            };
            viewSummary: string;
            generateSummary: string;
        };
        summary: {
            title: string;
            waiting: string;
            failed: string;
            tldr: string;
            consensus: string;
            keyPoints: string;
            gaps: string;
            references: string;
            noSummary: string;
        };
        claims: {
            title: string;
            noClaims: string;
        };
        details: {
            title: string;
            created: string;
            runId: string;
        };
    };
};
